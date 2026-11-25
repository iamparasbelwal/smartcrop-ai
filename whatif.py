"""What-if chat, local prototype: fixed instruction rules plus real arithmetic.

The language model is not connected yet. This module keeps the chat usable and honest in the
meantime: it recognises a handful of plain-language instructions, moves shares in the recipe,
recomputes with `nutrition.py`, and writes the sort of reply the model will later write itself.
Nothing here calls a network service.
"""

from __future__ import annotations

import formulations
import ingredients
import nutrition

UNKNOWN_REPLY = (
    "I can rebalance protein, cost, sweetness, salt, texture, fibre, millet or soy in this "
    "prototype. Try “more protein” or “cheaper”. The language model is not connected yet, "
    "so this reply comes from local rules."
)

# (label, keywords, moves). Keywords are matched in order, so narrower phrases come first.
RULES: list[tuple[str, tuple[str, ...], list[tuple[str, float]]]] = [
    ("Less protein", ("less protein", "lower protein", "reduce protein"), [("ING-005", -8.0), ("ING-010", 8.0)]),
    ("More protein", ("more protein", "boost protein", "high protein", "protein"), [("ING-005", 8.0), ("ING-010", -8.0)]),
    ("Lower cost", ("cheap", "cheaper", "cost", "budget", "price", "lower cost", "reduce cost", "economical"), [("ING-005", -6.0), ("ING-010", 6.0)]),
    ("Less sweet", ("less sweet", "less sugar", "sugar", "lower sugar", "reduce sugar"), [("ING-012", -4.0), ("ING-010", 4.0)]),
    ("Sweeter", ("sweet", "sweeter", "more sweet", "more sugar"), [("ING-012", 4.0), ("ING-010", -4.0)]),
    ("Less salt", ("less salt", "lower salt", "reduce sodium", "sodium", "less sodium"), [("ING-014", -0.5), ("ING-010", 0.5)]),
    ("Saltier", ("salt", "salty", "more salt"), [("ING-014", 0.5), ("ING-010", -0.5)]),
    ("Firmer texture", ("texture", "smooth", "binding", "crumb", "binder", "firm"), [("ING-013", 0.5), ("ING-010", -0.5)]),
    ("More fibre", ("fibre", "fiber", "high fibre", "high fiber", "more fibre", "more fiber"), [("ING-005", 4.0), ("ING-001", 4.0), ("ING-010", -8.0)]),
    ("More millet / bajra", ("millet", "bajra", "pearl millet", "millet flour"), [("ING-001", 8.0), ("ING-010", -8.0)]),
    ("More ragi / finger millet", ("ragi", "finger millet"), [("ING-002", 8.0), ("ING-010", -8.0)]),
    ("More soy", ("more soy", "soya", "defatted soy"), [("ING-005", 6.0), ("ING-010", -6.0)]),
    ("Swap soy for chickpea / besan", ("chickpea", "besan", "gram flour", "swap soy"), [("ING-005", -10.0), ("ING-007", 10.0)]),
    ("More lentils / dal", ("lentil", "lentils", "dal", "masoor", "moong"), [("ING-008", 8.0), ("ING-010", -8.0)]),
]


def _synthesize_from_db(
    instruction: str,
    *,
    project_name: str = "",
    project_description: str = "",
) -> tuple[list[tuple[str, float]], str]:
    """Query data/ingredients.csv dynamically when starting an empty project offline."""
    text = f"{project_name} {project_description} {instruction}".lower()
    all_crops = {r["ingredient_id"]: r for r in ingredients.list_ingredients()}

    clean_strict = any(w in text for w in ("clean", "additive", "synthetic", "natural", "minimum"))
    savory = any(w in text for w in ("pasta", "noodle", "savory", "savoury", "namkeen", "roti", "flatbread"))
    khoya = any(w in text for w in ("khoya", "mawa", "mithai", "milk", "creamy"))
    sweet = (not savory) and (khoya or any(w in text for w in ("biscuit", "cookie", "sweet", "bar", "jaggery")))
    gluten_free = any(w in text for w in ("gluten-free", "gluten free", "millet", "pasta"))
    high_protein = any(w in text for w in ("protein", "muscle", "dal", "lentil", "legume", "pulse"))

    if khoya:
        recipe = [("ING-015", 20.0), ("ING-007", 30.0), ("ING-010", 24.0), ("ING-012", 16.0), ("ING-017", 10.0)]
    elif any(w in text for w in ("pasta", "noodle")):
        recipe = [("ING-008", 40.0), ("ING-009", 25.0), ("ING-010", 33.5), ("ING-013", 1.5)]
    else:
        base_id = "ING-002" if "ragi" in text or "finger" in text else ("ING-003" if "jowar" in text else "ING-001")
        protein_id = "ING-007" if clean_strict or "chickpea" in text or "besan" in text else "ING-008"
        second_protein = "ING-016" if high_protein and "ING-016" in all_crops else "ING-009"
        recipe = [(base_id, 46.0), (protein_id, 26.0)]
        if second_protein != protein_id:
            recipe.append((second_protein, 14.0))
        if sweet and not any(w in text for w in ("zero sugar", "no sugar")):
            sweet_pct = 8.0 if any(w in text for w in ("less sugar", "low sugar")) else 12.0
            recipe.append(("ING-012", sweet_pct))
        used = sum(p for _, p in recipe)
        rem = round(100.0 - used, 1)
        if rem > 2.0:
            recipe.append(("ING-014", 1.5))
            recipe.append(("ING-010", round(rem - 1.5, 1)))
        elif rem > 0:
            recipe.append(("ING-014", rem))

    ok, validated, _ = formulations.validate_items(recipe)
    if not ok:
        validated = formulations.starter_items()
    resolved = formulations.resolve(validated)
    blend = nutrition.blend_nutrition(resolved)
    cost = nutrition.cost_per_kg(resolved)
    names = ", ".join(r["ingredient"]["name"].lower() for r in resolved)
    return (
        validated,
        f"Selected crops from the local database ({names}) matching your project goals "
        f"({'gluten-free ' if gluten_free else ''}{'clean-label ' if clean_strict else ''}"
        f"{'savory' if savory else 'formulation'}). Protein {blend['protein_g']:.1f} g per 100 g, "
        f"energy {blend['energy_kcal']:.0f} kcal, cost ₹{cost:,.2f} per kg.",
    )


def apply(
    items: list[tuple[str, float]],
    instruction: str,
    *,
    project_name: str = "",
    project_description: str = "",
) -> tuple[list[tuple[str, float]], str, bool]:
    """Return (new items, reply, changed) for one chat instruction."""
    text = (instruction or "").strip().lower()
    if not text:
        return items, "", False

    if not items:
        new_items, reply = _synthesize_from_db(
            instruction, project_name=project_name, project_description=project_description
        )
        return new_items, reply, bool(new_items)

    for label, keywords, moves in RULES:
        if any(word in text for word in keywords):
            new_items = _move(items, moves)
            return new_items, _reply(label, items, new_items), new_items != items

    return items, UNKNOWN_REPLY, False


def _move(items: list[tuple[str, float]], moves: list[tuple[str, float]]) -> list[tuple[str, float]]:
    """Apply share deltas, keeping every share non-negative and the total at 100 %."""
    shares = {ingredient_id: share for ingredient_id, share in items}
    for ingredient_id, delta in moves:
        shares[ingredient_id] = max(0.0, shares.get(ingredient_id, 0.0) + delta)

    drift = 100.0 - sum(shares.values())
    if abs(drift) > 0.001:
        filler = next((key for key in ("ING-010", "ING-001") if key in shares), next(iter(shares)))
        shares[filler] = max(0.0, shares[filler] + drift)

    return [(ingredient_id, round(share, 1)) for ingredient_id, share in shares.items() if share > 0]


def _reply(label: str, before_items: list[tuple[str, float]], after_items: list[tuple[str, float]]) -> str:
    before_shares = dict(before_items)
    after_shares = dict(after_items)

    changes = []
    for ingredient_id, share in before_shares.items():
        new_share = after_shares.get(ingredient_id, 0.0)
        if abs(new_share - share) < 0.05:
            continue
        ingredient = ingredients.get_ingredient(ingredient_id)
        name = ingredient["name"].lower() if ingredient else ingredient_id
        changes.append(f"{name} {share:g} → {new_share:g}%")

    before = nutrition.blend_nutrition(formulations.resolve(before_items))
    after = nutrition.blend_nutrition(formulations.resolve(after_items))
    cost_before = nutrition.cost_per_kg(formulations.resolve(before_items))
    cost_after = nutrition.cost_per_kg(formulations.resolve(after_items))

    moved = "; ".join(changes) if changes else "no share moved"
    return (
        f"{label}: {moved}. Protein {before['protein_g']:.1f} → {after['protein_g']:.1f} g per "
        f"100 g, energy {before['energy_kcal']:.0f} → {after['energy_kcal']:.0f} kcal, cost "
        f"₹{cost_before:,.2f} → ₹{cost_after:,.2f} per kg."
    )
