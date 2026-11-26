"""The workbench co-pilot: Gemini proposes, Python validates and does the arithmetic.

Every model answer passes through here before it can touch the recipe, so the page only ever
sees a validated recipe plus figures computed from the crop database. When Gemini is missing or
unreachable the local rules in `whatif.py` take over and the reply says so honestly.
"""

from __future__ import annotations

import cleanlabel
import formulations
import gemini
import ingredients
import nutrition
import regions
import whatif


def _facts(
    items: list[tuple[str, float]],
    before_items: list[tuple[str, float]] | None = None,
    *,
    target_region: str = "Pan-India",
) -> str:
    """One line of real numbers, computed here and handed to the model's answer."""
    recipe = formulations.resolve(items)
    blend = nutrition.blend_nutrition(recipe)
    cost = nutrition.cost_per_kg(recipe)
    reg = regions.evaluate_blend(recipe, target_region)
    reg_note = (
        f" · {reg['local_share_pct']}% local/nearby for {reg['target_region']} "
        f"(landed ₹{reg['landed_cost_per_kg']:,.2f}/kg)"
        if reg["is_targeted"]
        else ""
    )

    if before_items:
        old = nutrition.blend_nutrition(formulations.resolve(before_items))
        old_cost = nutrition.cost_per_kg(formulations.resolve(before_items))
        return (
            f"protein {old['protein_g']:.1f} → {blend['protein_g']:.1f} g, "
            f"energy {old['energy_kcal']:.0f} → {blend['energy_kcal']:.0f} kcal, "
            f"fibre {old['fibre_g']:.1f} → {blend['fibre_g']:.1f} g per 100 g, "
            f"cost ₹{old_cost:,.2f} → ₹{cost:,.2f} per kg{reg_note}"
        )
    return (
        f"protein {blend['protein_g']:.1f} g, energy {blend['energy_kcal']:.0f} kcal, "
        f"fibre {blend['fibre_g']:.1f} g per 100 g, cost ₹{cost:,.2f} per kg{reg_note}"
    )


def _moved_names(items: list[tuple[str, float]], before_items: list[tuple[str, float]]) -> list[str]:
    before = dict(before_items)
    after = dict(items)
    moves = []
    for ingredient_id in dict.fromkeys([key for key, _ in before_items] + [key for key, _ in items]):
        old_share = before.get(ingredient_id, 0.0)
        new_share = after.get(ingredient_id, 0.0)
        if abs(old_share - new_share) < 0.05:
            continue
        ingredient = ingredients.get_ingredient(ingredient_id)
        name = ingredient["name"] if ingredient else ingredient_id
        if old_share <= 0:
            moves.append(f"{name} {new_share:.1f}%")
        elif new_share <= 0:
            moves.append(f"{name} removed")
        else:
            moves.append(f"{name} {old_share:.1f}% → {new_share:.1f}%")
    return moves


def prepare_db_context(
    instruction: str,
    *,
    project_name: str = "",
    project_description: str = "",
    target_region: str = "Pan-India",
) -> dict[str, object]:
    """Query the local CSV crop, source, and additive database before calling Gemini."""
    all_crops = ingredients.list_ingredients()
    watchlist = cleanlabel.watchlist()
    combined = f"{project_name} {project_description} {instruction}".lower()
    resolved_region = regions.detect_target_region(
        instruction,
        explicit_region=target_region,
        project_text=f"{project_name} {project_description}",
    )

    clean_strict = any(
        term in combined
        for term in ("clean", "additive", "synthetic", "natural", "chemical", "no preservative")
    )
    dairy_free = any(term in combined for term in ("vegan", "dairy-free", "plant-based", "no dairy"))
    gluten_free = any(term in combined for term in ("gluten-free", "gluten free", "millet"))

    clean_proteins = [
        row["name"]
        for row in all_crops
        if ingredients.number(row, "protein_g") >= 20.0
        and row.get("is_clean_label") == "yes"
        and (not dairy_free or row.get("category") != "Dairy")
    ]
    flagged_items = [
        f"{row['name']} ({row.get('clean_label_note') or 'check'})"
        for row in all_crops
        if row.get("is_clean_label") != "yes"
    ]
    low_cost_bases = [
        row["name"]
        for row in all_crops
        if ingredients.number(row, "cost_per_kg") <= 60.0
        and row.get("category") in {"Millet", "Cereal", "Legume", "Pulse"}
        and (not gluten_free or row["ingredient_id"] != "ING-011")
    ]

    brief_lines = [
        f"- Database holds {len(all_crops)} crops/ingredients and {len(watchlist)} additive watchlist rules.",
        f"- Clean-label (yes) high-protein sources (>=20g/100g): {', '.join(clean_proteins) or 'None'}.",
        f"- Affordable crop bases (<=Rs 60/kg): {', '.join(low_cost_bases) or 'None'}.",
    ]
    if resolved_region != "Pan-India":
        local_ranked = []
        distant_names = []
        for row in all_crops:
            if dairy_free and row.get("category") == "Dairy":
                continue
            if clean_strict and row.get("is_clean_label") != "yes":
                continue
            if gluten_free and row["ingredient_id"] == "ING-011":
                continue
            landed, tier, _ = regions.effective_cost_per_kg(row, resolved_region)
            if tier in ("LOCAL", "NEARBY"):
                local_ranked.append((landed, tier, f"{row['name']} ({tier} {row.get('region')}, landed ₹{landed:.0f}/kg)"))
            elif row.get("category") in {"Millet", "Cereal", "Pulse", "Legume"}:
                distant_names.append(f"{row['name']} ({row.get('region')}, +₹{regions.FREIGHT_DISTANT:.0f}/kg freight)")
        local_ranked.sort(key=lambda x: (0 if x[1] == "LOCAL" else 1, x[0]))
        brief_lines.append(
            f"- TARGET MARKET REGION: {resolved_region} — aim for >=65-75% of dry weight from [LOCAL] & [NEARBY] crops to cut logistics cost."
        )
        brief_lines.append(
            f"- Regional cost-optimized crops for {resolved_region}: {', '.join(x[2] for x in local_ranked[:7]) or 'Use lowest landed-cost bases'}."
        )
        if distant_names:
            brief_lines.append(
                f"- Higher-freight distant staples for {resolved_region}: {', '.join(distant_names[:5])}."
            )
    if flagged_items:
        brief_lines.append(
            f"- Flagged/review items in DB: {', '.join(flagged_items)}"
            + (" (EXCLUDE because clean-label / minimum additives requested)." if clean_strict else ".")
        )

    return {
        "crop_count": len(all_crops),
        "watchlist_count": len(watchlist),
        "clean_strict": clean_strict,
        "target_region": resolved_region,
        "summary": "\n".join(brief_lines),
    }


def chat(
    items: list[tuple[str, float]],
    instruction: str,
    *,
    project_name: str = "",
    project_description: str = "",
    target_region: str = "Pan-India",
    db_brief: str = "",
    history: list[dict] | None = None,
    model: str | None = None,
) -> dict:
    """One chat turn. Returns reply, validated recipe (or None), engine, notes, and reasoning trace."""
    instruction = (instruction or "").strip()
    if not instruction:
        return {"reply": "", "items": None, "engine": "none", "notes": [], "thought": "", "thought_summary": ""}

    recipe_rows = formulations.resolve(items) if items else []
    db_ctx = prepare_db_context(
        instruction,
        project_name=project_name,
        project_description=project_description,
        target_region=target_region,
    )
    resolved_region = str(db_ctx.get("target_region") or target_region or "Pan-India")
    if not db_brief:
        db_brief = str(db_ctx["summary"])
    crop_count = int(db_ctx["crop_count"])

    try:
        answer = gemini.discuss(
            instruction,
            recipe_rows,
            project_name=project_name,
            project_description=project_description,
            target_region=resolved_region,
            db_brief=db_brief,
            history=history,
            model=model,
        )
    except gemini.GeminiError as exc:
        local_items, local_reply, changed = whatif.apply(
            items,
            instruction,
            project_name=project_name,
            project_description=project_description,
            target_region=resolved_region,
        )
        return {
            "reply": f"{local_reply}\n\n(Cloud AI models are temporarily busy — {exc} Local database rules answered instead.)",
            "items": local_items if changed else None,
            "engine": "local",
            "notes": [],
            "target_region": resolved_region,
            "thought": f"Cloud models temporarily unavailable ({exc}). Screened {crop_count} local DB crops for {resolved_region} goals.",
            "thought_summary": f"Screened {crop_count} local DB crops (offline fallback)",
        }

    reply = answer["reply"]
    reasoning_parts = [p for p in (answer.get("reasoning"), answer.get("selected_notes")) if p]
    thought = "\n\n".join(reasoning_parts)
    thought_summary = f"Inspected {crop_count} DB crops ({resolved_region})"

    proposed = answer.get("recipe")
    if not proposed:
        return {
            "reply": reply,
            "items": None,
            "engine": gemini.model_name(),
            "notes": [],
            "target_region": resolved_region,
            "thought": thought,
            "thought_summary": thought_summary,
        }

    ok, validated, notes = formulations.validate_items(proposed)
    if not ok:
        return {
            "reply": reply + "\n\nI could not turn that into a valid recipe, so the blend is unchanged.",
            "items": None,
            "engine": gemini.model_name(),
            "notes": notes,
            "target_region": resolved_region,
            "thought": thought,
            "thought_summary": thought_summary,
        }

    if items and validated == [(key, round(value, 1)) for key, value in items]:
        return {
            "reply": reply,
            "items": None,
            "engine": gemini.model_name(),
            "notes": notes,
            "target_region": resolved_region,
            "thought": thought,
            "thought_summary": thought_summary,
        }

    moves = _moved_names(validated, items)
    lines = [reply]
    if moves:
        prefix = "Moved: " if items else "Selected from database: "
        lines.append(prefix + "; ".join(moves[:7]) + ".")
    lines.append("Computed here, not by the model: " + _facts(validated, items or None, target_region=resolved_region) + ".")
    if notes:
        lines.append("Checks applied: " + "; ".join(notes) + ".")
    fallback_reason = str(gemini._config.get("last_fallback_reason") or "")
    used_engine = gemini.model_name()
    return {
        "reply": "\n".join(lines),
        "items": validated,
        "engine": used_engine,
        "requested_model": model or "",
        "fallback_reason": fallback_reason if (model and used_engine != model) else "",
        "notes": notes,
        "target_region": resolved_region,
        "thought": thought,
        "thought_summary": f"Extracted {len(validated)} crops for {resolved_region} from {crop_count} DB entries",
    }


def draft(
    brief: str,
    *,
    project_name: str = "",
    cook: str = "",
    model: str | None = None,
) -> dict:
    """A new candidate recipe from a written brief, validated before use."""
    try:
        answer = gemini.draft(brief, project_name=project_name, cook=cook, model=model)
    except gemini.GeminiError as exc:
        return {"ok": False, "reason": str(exc)}

    ok, items, notes = formulations.validate_items(answer.get("recipe") or [])
    if not ok:
        return {
            "ok": False,
            "reason": answer.get("rationale") or "The model did not return a usable recipe.",
            "notes": notes,
        }

    recipe = formulations.resolve(items)
    blend = nutrition.blend_nutrition(recipe)
    cost = nutrition.cost_per_kg(recipe)
    findings = cleanlabel.check(recipe)
    return {
        "ok": True,
        "name": answer.get("name") or "AI draft",
        "rationale": answer.get("rationale") or "",
        "items": items,
        "notes": notes,
        "blend": blend,
        "cost": cost,
        "findings": findings,
        "engine": gemini.model_name(),
    }


def explain_blend(items: list[tuple[str, float]], *, model: str | None = None) -> str:
    recipe = formulations.resolve(items)
    blend = nutrition.blend_nutrition(recipe)
    cost = nutrition.cost_per_kg(recipe)
    return gemini.explain_blend(recipe, blend, cost, model=model)


def explain_clean_label(findings: list[dict], *, model: str | None = None) -> str:
    return gemini.explain_clean_label(findings, model=model)
