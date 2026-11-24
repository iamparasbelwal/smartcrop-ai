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


def apply(items: list[tuple[str, float]], instruction: str) -> tuple[list[tuple[str, float]], str, bool]:
    """Return (new items, reply, changed) for one chat instruction."""
    text = (instruction or "").strip().lower()
    if not text:
        return items, "", False

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
