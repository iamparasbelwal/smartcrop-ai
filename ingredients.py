"""Ingredient database: seeded local crops with nutrition, cost and confidence tags.

Every number carries two separate confidences — one for nutrition, one for cost — plus a
source id pointing at `sources.csv`. The seed is deliberately marked ``estimated``: these are
plausible reference ranges for the demo, not lab measurements, and the note says so.

Nothing here does arithmetic on a formulation; it only answers "what is this ingredient".
"""

from __future__ import annotations

import auth
from storage import DATA_DIR, now, read_csv, write_csv

INGREDIENTS_CSV = DATA_DIR / "ingredients.csv"
SOURCES_CSV = DATA_DIR / "sources.csv"

SOURCE_FIELDS = ["source_id", "title", "publisher", "year", "url", "note", "added_at"]
INGREDIENT_FIELDS = [
    "ingredient_id",
    "name",
    "local_name",
    "category",
    "region",
    "energy_kcal",
    "protein_g",
    "fat_g",
    "carbs_g",
    "fibre_g",
    "moisture_g",
    "nutrition_basis",
    "nutrition_confidence",
    "cost_per_kg",
    "cost_basis",
    "cost_date",
    "cost_confidence",
    "is_clean_label",
    "clean_label_note",
    "max_practical_pct",
    "source_id",
    "updated_at",
]

SEED_SOURCES = [
    {
        "source_id": "S-001",
        "title": "Demo seed: approximate composition ranges from public nutrition references",
        "publisher": "Team seed data",
        "year": "2026",
        "url": "",
        "note": "Not lab-verified. Replace with IFCT 2017 values or lab measurements before quoting as fact.",
    },
    {
        "source_id": "S-002",
        "title": "Local mandi retail prices, team spot survey",
        "publisher": "Team seed data",
        "year": "2026",
        "url": "",
        "note": "Single-day retail prices, no invoice trail.",
    },
    {
        "source_id": "S-003",
        "title": "Supplier specification sheet (grade-dependent)",
        "publisher": "Team seed data",
        "year": "2026",
        "url": "",
        "note": "Fibre content of guar gum varies widely by grade; treat as unknown until sampled.",
    },
]

# (id, name, local name, category, region, energy, protein, fat, carbs, fibre, moisture,
#  nutrition_confidence, cost_per_kg, cost_confidence, clean_label, clean_label_note,
#  max_practical_pct, source_id)
SEED_INGREDIENTS = [
    ("ING-001", "Pearl millet flour", "Bajra atta", "Millet", "Rajasthan",
     361, 11.6, 5.0, 67.5, 11.3, 12.4, "estimated", 45.0, "estimated",
     "yes", "Single-ingredient stone-milled flour", 60, "S-001"),
    ("ING-002", "Finger millet flour", "Ragi atta", "Millet", "Karnataka",
     328, 7.3, 1.3, 72.0, 11.5, 11.5, "estimated", 55.0, "estimated",
     "yes", "Single-ingredient flour", 60, "S-001"),
    ("ING-003", "Sorghum flour", "Jowar atta", "Millet", "Maharashtra",
     349, 10.4, 1.9, 72.6, 9.7, 11.9, "estimated", 42.0, "estimated",
     "yes", "Single-ingredient flour", 60, "S-001"),
    ("ING-004", "Foxtail millet", "Kangni", "Millet", "Andhra Pradesh",
     351, 12.3, 4.3, 65.8, 8.0, 11.3, "estimated", 70.0, "estimated",
     "yes", "Whole grain, no additives", 50, "S-001"),
    ("ING-005", "Defatted soy flour", "Soy atta", "Legume", "Madhya Pradesh",
     331, 47.0, 1.5, 32.5, 17.5, 8.0, "estimated", 95.0, "estimated",
     "check", "Hexane-extracted; ask supplier for residue spec", 25, "S-001"),
    ("ING-006", "Whole soybean", "Soybean", "Legume", "Madhya Pradesh",
     446, 36.5, 19.9, 30.2, 9.3, 8.5, "estimated", 60.0, "estimated",
     "yes", "Whole legume, needs heat treatment", 20, "S-001"),
    ("ING-007", "Chickpea flour", "Besan", "Pulse", "Madhya Pradesh",
     372, 22.5, 5.6, 57.8, 10.8, 9.5, "estimated", 110.0, "estimated",
     "yes", "Single-ingredient milled gram", 40, "S-001"),
    ("ING-008", "Red lentil dal", "Masoor dal", "Pulse", "Madhya Pradesh",
     346, 25.0, 1.1, 59.0, 11.0, 12.0, "estimated", 95.0, "estimated",
     "yes", "Split, hulled legume", 40, "S-001"),
    ("ING-009", "Green gram flour", "Moong atta", "Pulse", "Rajasthan",
     347, 24.0, 1.3, 59.9, 8.0, 11.0, "estimated", 120.0, "estimated",
     "yes", "Single-ingredient milled gram", 35, "S-001"),
    ("ING-010", "Rice flour", "Chawal atta", "Cereal", "West Bengal",
     357, 7.0, 1.4, 79.0, 2.4, 11.5, "estimated", 45.0, "estimated",
     "yes", "Milled rice, no additives", 50, "S-001"),
    ("ING-011", "Wheat flour", "Gehun atta", "Cereal", "Punjab",
     341, 12.1, 1.7, 69.4, 11.0, 12.0, "estimated", 38.0, "estimated",
     "yes", "Whole wheat, stone-milled", 70, "S-001"),
    ("ING-012", "Jaggery", "Gud", "Sweetener", "Maharashtra",
     383, 0.4, 0.1, 95.0, 0.0, 4.0, "estimated", 48.0, "estimated",
     "yes", "Unrefined cane sugar, no sulphur", 20, "S-002"),
    ("ING-013", "Guar gum", "Guar", "Hydrocolloid", "Rajasthan",
     199, 4.6, 0.6, 86.5, 80.0, 9.0, "unknown", 210.0, "estimated",
     "yes", "Seed galactomannan, used under 1%", 2, "S-003"),
    ("ING-014", "Iodised salt", "Namak", "Seasoning", "Gujarat",
     0, 0.0, 0.0, 0.0, 0.0, 0.2, "estimated", 12.0, "estimated",
     "yes", "Iodised table salt", 2, "S-002"),
    ("ING-015", "Skim milk powder", "SMP", "Dairy", "Gujarat",
     351, 34.0, 0.8, 52.0, 0.0, 3.5, "estimated", 320.0, "estimated",
     "yes", "Spray-dried skim milk", 20, "S-001"),
    ("ING-016", "Defatted groundnut flour", "Moongphali atta", "Oilseed", "Gujarat",
     354, 45.0, 6.0, 30.0, 8.0, 7.0, "estimated", 140.0, "estimated",
     "yes", "Pressed cake, milled", 30, "S-001"),
    ("ING-017", "Sesame seeds", "Til", "Oilseed", "Rajasthan",
     573, 17.7, 49.7, 23.4, 11.8, 4.8, "estimated", 170.0, "estimated",
     "yes", "Whole hulled seed", 10, "S-001"),
]


def bootstrap() -> None:
    """Create the two CSVs and seed them the first time they are empty."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if not read_csv(SOURCES_CSV, SOURCE_FIELDS):
        write_csv(
            SOURCES_CSV,
            SOURCE_FIELDS,
            [source | {"added_at": now()} for source in SEED_SOURCES],
        )

    if not read_csv(INGREDIENTS_CSV, INGREDIENT_FIELDS):
        write_csv(
            INGREDIENTS_CSV,
            INGREDIENT_FIELDS,
            [
                {
                    "ingredient_id": ingredient_id,
                    "name": name,
                    "local_name": local_name,
                    "category": category,
                    "region": region,
                    "energy_kcal": energy,
                    "protein_g": protein,
                    "fat_g": fat,
                    "carbs_g": carbs,
                    "fibre_g": fibre,
                    "moisture_g": moisture,
                    "nutrition_basis": "as-is per 100 g",
                    "nutrition_confidence": nutrition_confidence,
                    "cost_per_kg": cost_per_kg,
                    "cost_basis": "retail, local mandi spot price",
                    "cost_date": "2026-11-20",
                    "cost_confidence": cost_confidence,
                    "is_clean_label": clean_label,
                    "clean_label_note": clean_label_note,
                    "max_practical_pct": max_practical_pct,
                    "source_id": source_id,
                    "updated_at": now(),
                }
                for (
                    ingredient_id,
                    name,
                    local_name,
                    category,
                    region,
                    energy,
                    protein,
                    fat,
                    carbs,
                    fibre,
                    moisture,
                    nutrition_confidence,
                    cost_per_kg,
                    cost_confidence,
                    clean_label,
                    clean_label_note,
                    max_practical_pct,
                    source_id,
                ) in SEED_INGREDIENTS
            ],
        )


def list_ingredients() -> list[dict[str, str]]:
    rows = read_csv(INGREDIENTS_CSV, INGREDIENT_FIELDS)
    rows.sort(key=lambda row: (row["category"], row["name"].lower()))
    return rows


def get_ingredient(ingredient_id: str) -> dict[str, str] | None:
    return next(
        (row for row in read_csv(INGREDIENTS_CSV, INGREDIENT_FIELDS) if row["ingredient_id"] == ingredient_id),
        None,
    )


def get_source(source_id: str) -> dict[str, str] | None:
    return next((row for row in read_csv(SOURCES_CSV, SOURCE_FIELDS) if row["source_id"] == source_id), None)


def number(row: dict[str, str], field: str) -> float:
    """Parse one numeric column, treating blanks and junk as 0."""
    try:
        return float(row.get(field) or 0)
    except (TypeError, ValueError):
        return 0.0


def cost_per_100g(ingredient: dict[str, str]) -> float:
    """Ingredient cost for 100 g, derived from the per-kg mandi price."""
    return number(ingredient, "cost_per_kg") / 10


CONFIDENCE_LEVELS = ("verified", "estimated", "unknown")


def verified_counts() -> dict[str, int]:
    """How much of the ingredient table a person has actually checked."""
    rows = read_csv(INGREDIENTS_CSV, INGREDIENT_FIELDS)
    return {
        "ingredients": len(rows),
        "nutrition_verified": sum(1 for row in rows if row["nutrition_confidence"] == "verified"),
        "cost_verified": sum(1 for row in rows if row["cost_confidence"] == "verified"),
        "nutrition_unknown": sum(1 for row in rows if row["nutrition_confidence"] == "unknown"),
    }


# --------------------------------------------------------------------------- #
# Correcting values (admin verification)
# --------------------------------------------------------------------------- #
NUMERIC_FIELDS: dict[str, dict[str, object]] = {
    "energy_kcal": {"label": "Energy (kcal / 100 g)", "step": 1.0, "format": "%.0f"},
    "protein_g": {"label": "Protein (g / 100 g)", "step": 0.1, "format": "%.1f"},
    "fat_g": {"label": "Fat (g / 100 g)", "step": 0.1, "format": "%.1f"},
    "carbs_g": {"label": "Carbs (g / 100 g)", "step": 0.1, "format": "%.1f"},
    "fibre_g": {"label": "Fibre (g / 100 g)", "step": 0.1, "format": "%.1f"},
    "moisture_g": {"label": "Moisture (g / 100 g)", "step": 0.1, "format": "%.1f"},
    "cost_per_kg": {"label": "Cost (₹ / kg)", "step": 0.5, "format": "%.2f"},
}
EDIT_FIELDS = tuple(NUMERIC_FIELDS)
COST_FIELD = "cost_per_kg"


def display_value(field: str, value: float) -> str:
    """How one number reads in the audit log."""
    if field == COST_FIELD:
        return f"₹{value:,.2f} / kg"
    if field == "energy_kcal":
        return f"{value:,.0f} kcal / 100 g"
    return f"{value:,.1f} g / 100 g"


def save_verification(
    ingredient_id: str,
    values: dict[str, float],
    nutrition_confidence: str,
    cost_confidence: str,
    actor_id: str,
    reference: str = "",
    lab_report: str = "",
) -> tuple[bool, str]:
    """Write corrected values and confidence tags, auditing every field that moved."""
    if nutrition_confidence not in CONFIDENCE_LEVELS or cost_confidence not in CONFIDENCE_LEVELS:
        return False, "Unknown confidence value."

    rows = read_csv(INGREDIENTS_CSV, INGREDIENT_FIELDS)
    target = next((row for row in rows if row["ingredient_id"] == ingredient_id), None)
    if target is None:
        return False, "Ingredient not found."

    reference = (reference or "").strip()
    changed: list[tuple[str, str, str]] = []
    for field in EDIT_FIELDS:
        if field not in values:
            continue
        try:
            new_value = round(float(values[field]), 2)
        except (TypeError, ValueError):
            return False, f"{NUMERIC_FIELDS[field]['label']} is not a number."
        old_value = number(target, field)
        if abs(new_value - old_value) < 0.005:
            continue
        changed.append((field, display_value(field, old_value), display_value(field, new_value)))
        target[field] = f"{new_value:g}"

    old_confidence = f"nutrition {target['nutrition_confidence']}, cost {target['cost_confidence']}"
    confidence_changed = (
        target["nutrition_confidence"] != nutrition_confidence
        or target["cost_confidence"] != cost_confidence
    )

    if not changed and not confidence_changed:
        return False, "Nothing changed — the values and checks are already what you see."
    if changed and not reference:
        return False, "Say what you checked the new values against before saving."

    target["nutrition_confidence"] = nutrition_confidence
    target["cost_confidence"] = cost_confidence
    target["updated_at"] = now()
    write_csv(INGREDIENTS_CSV, INGREDIENT_FIELDS, rows)

    suffix = f": {reference}" if reference else ""
    for field, old_text, new_text in changed:
        auth.log_event(
            actor_id,
            table="ingredients",
            record_id=ingredient_id,
            field=field,
            old_value=old_text,
            new_value=new_text,
            note=f"Value corrected on verification{suffix}",
            lab_report=lab_report,
        )

    new_confidence = f"nutrition {nutrition_confidence}, cost {cost_confidence}"
    if confidence_changed:
        auth.log_event(
            actor_id,
            table="ingredients",
            record_id=ingredient_id,
            field="nutrition_confidence, cost_confidence",
            old_value=old_confidence,
            new_value=new_confidence,
            note=f"Lab verification recorded{suffix}",
            lab_report=lab_report,
        )

    parts: list[str] = []
    if changed:
        parts.append(f"{len(changed)} value{'s' if len(changed) != 1 else ''} updated")
    if confidence_changed:
        parts.append(new_confidence)
    if lab_report:
        parts.append("lab report attached")
    return True, f"{target['name']}: " + ", ".join(parts) + "."
