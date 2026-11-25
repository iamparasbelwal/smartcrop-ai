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
import whatif


def _facts(items: list[tuple[str, float]], before_items: list[tuple[str, float]] | None = None) -> str:
    """One line of real numbers, computed here and handed to the model's answer."""
    recipe = formulations.resolve(items)
    blend = nutrition.blend_nutrition(recipe)
    cost = nutrition.cost_per_kg(recipe)

    if before_items:
        old = nutrition.blend_nutrition(formulations.resolve(before_items))
        old_cost = nutrition.cost_per_kg(formulations.resolve(before_items))
        return (
            f"protein {old['protein_g']:.1f} → {blend['protein_g']:.1f} g, "
            f"energy {old['energy_kcal']:.0f} → {blend['energy_kcal']:.0f} kcal, "
            f"fibre {old['fibre_g']:.1f} → {blend['fibre_g']:.1f} g per 100 g, "
            f"cost ₹{old_cost:,.2f} → ₹{cost:,.2f} per kg"
        )
    return (
        f"protein {blend['protein_g']:.1f} g, energy {blend['energy_kcal']:.0f} kcal, "
        f"fibre {blend['fibre_g']:.1f} g per 100 g, cost ₹{cost:,.2f} per kg"
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
) -> dict[str, object]:
    """Query the local CSV crop, source, and additive database before calling Gemini."""
    all_crops = ingredients.list_ingredients()
    watchlist = cleanlabel.watchlist()
    combined = f"{project_name} {project_description} {instruction}".lower()

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
    if flagged_items:
        brief_lines.append(
            f"- Flagged/review items in DB: {', '.join(flagged_items)}"
            + (" (EXCLUDE because clean-label / minimum additives requested)." if clean_strict else ".")
        )

    return {
        "crop_count": len(all_crops),
        "watchlist_count": len(watchlist),
        "clean_strict": clean_strict,
        "summary": "\n".join(brief_lines),
    }


def chat(
    items: list[tuple[str, float]],
    instruction: str,
    *,
    project_name: str = "",
    project_description: str = "",
    db_brief: str = "",
    history: list[dict] | None = None,
) -> dict:
    """One chat turn. Returns reply, validated recipe (or None), engine, notes, and reasoning trace."""
    instruction = (instruction or "").strip()
    if not instruction:
        return {"reply": "", "items": None, "engine": "none", "notes": [], "thought": "", "thought_summary": ""}

    recipe_rows = formulations.resolve(items) if items else []
    if not db_brief:
        db_ctx = prepare_db_context(
            instruction, project_name=project_name, project_description=project_description
        )
        db_brief = str(db_ctx["summary"])
        crop_count = int(db_ctx["crop_count"])
    else:
        crop_count = len(ingredients.list_ingredients())

    try:
        answer = gemini.discuss(
            instruction,
            recipe_rows,
            project_name=project_name,
            project_description=project_description,
            db_brief=db_brief,
            history=history,
        )
    except gemini.GeminiError as exc:
        local_items, local_reply, changed = whatif.apply(
            items,
            instruction,
            project_name=project_name,
            project_description=project_description,
        )
        return {
            "reply": f"{local_reply}\n\n(Gemini is temporarily busy — {exc} Local database rules answered instead.)",
            "items": local_items if changed else None,
            "engine": "local",
            "notes": [],
            "thought": f"Cloud models temporarily unavailable ({exc}). Screened {crop_count} local DB crops for project goals.",
            "thought_summary": f"Screened {crop_count} local DB crops (offline fallback)",
        }

    reply = answer["reply"]
    reasoning_parts = [p for p in (answer.get("reasoning"), answer.get("selected_notes")) if p]
    thought = "\n\n".join(reasoning_parts)
    thought_summary = f"Inspected {crop_count} DB crops & additive rules"

    proposed = answer.get("recipe")
    if not proposed:
        return {
            "reply": reply,
            "items": None,
            "engine": gemini.model_name(),
            "notes": [],
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
            "thought": thought,
            "thought_summary": thought_summary,
        }

    if items and validated == [(key, round(value, 1)) for key, value in items]:
        return {
            "reply": reply,
            "items": None,
            "engine": gemini.model_name(),
            "notes": notes,
            "thought": thought,
            "thought_summary": thought_summary,
        }

    moves = _moved_names(validated, items)
    lines = [reply]
    if moves:
        prefix = "Moved: " if items else "Selected from database: "
        lines.append(prefix + "; ".join(moves[:7]) + ".")
    lines.append("Computed here, not by the model: " + _facts(validated, items or None) + ".")
    if notes:
        lines.append("Checks applied: " + "; ".join(notes) + ".")
    return {
        "reply": "\n".join(lines),
        "items": validated,
        "engine": gemini.model_name(),
        "notes": notes,
        "thought": thought,
        "thought_summary": f"Extracted {len(validated)} crops from {crop_count} DB entries",
    }


def draft(brief: str, *, project_name: str = "", cook: str = "") -> dict:
    """A new candidate recipe from a written brief, validated before use."""
    try:
        answer = gemini.draft(brief, project_name=project_name, cook=cook)
    except gemini.GeminiError as exc:
        return {"ok": False, "reason": str(exc)}

    ok, items, notes = formulations.validate_items(answer.get("recipe") or [])
    if not ok:
        return {
            "ok": False,
            "reason": answer.get("rationale") or "Gemini did not return a usable recipe.",
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


def explain_blend(items: list[tuple[str, float]]) -> str:
    recipe = formulations.resolve(items)
    blend = nutrition.blend_nutrition(recipe)
    cost = nutrition.cost_per_kg(recipe)
    return gemini.explain_blend(recipe, blend, cost)


def explain_clean_label(findings: list[dict]) -> str:
    return gemini.explain_clean_label(findings)
