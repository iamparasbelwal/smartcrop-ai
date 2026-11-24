"""Blend arithmetic: nutrition per 100 g and cost, computed in Python from ingredient rows.

This is the only place the blend's numbers come from. Gemini may explain a formulation, but it
never adds or multiplies these values — every figure in the workbench is a weighted sum of the
ingredient database here, so it can be checked by hand.
"""

from __future__ import annotations

import ingredients

SERVING_GRAMS = 40

# (field, label, unit, decimals)
NUTRIENT_ROWS = [
    ("energy_kcal", "Energy", "kcal", 0),
    ("protein_g", "Protein", "g", 1),
    ("fat_g", "Fat", "g", 1),
    ("carbs_g", "Carbohydrate", "g", 1),
    ("fibre_g", "Dietary fibre", "g", 1),
]


def blend_nutrition(rows: list[dict]) -> dict[str, float]:
    """Weighted sum per 100 g of blend: each ingredient's as-is value × its share."""
    return {
        field: round(
            sum(ingredients.number(row["ingredient"], field) * row["share_pct"] / 100 for row in rows),
            1,
        )
        for field, _, _, _ in NUTRIENT_ROWS
    }


def cost_per_kg(rows: list[dict]) -> float:
    """Ingredient cost of one kilogram of blend, from the per-kg mandi prices."""
    return sum(
        ingredients.number(row["ingredient"], "cost_per_kg") * row["share_pct"] / 100 for row in rows
    )


def cost_per_serving(rows: list[dict], serving_g: float = SERVING_GRAMS) -> float:
    return cost_per_kg(rows) * serving_g / 1000


def confidence_counts(rows: list[dict]) -> dict[str, int]:
    """How many ingredient rows behind this blend are verified / estimated / unknown."""
    counts = {"verified": 0, "estimated": 0, "unknown": 0}
    for row in rows:
        tag = row["ingredient"]["nutrition_confidence"] or "unknown"
        counts[tag] = counts.get(tag, 0) + 1
    return counts
