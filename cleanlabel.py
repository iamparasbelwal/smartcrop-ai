"""Clean-label check: a hand-written watchlist of synthetic terms, never an AI judgement.

The rulebook lives in `data/additives.csv` so it can be read, argued with and extended by the
lab. Detection is plain text matching against an ingredient's name and note, plus the
ingredient's own clean-label flag. Nothing here guesses: either a term is on the list or it is not.
"""

from __future__ import annotations

import ingredients
from storage import DATA_DIR, now, read_csv, write_csv

ADDITIVES_CSV = DATA_DIR / "additives.csv"
ADDITIVE_FIELDS = [
    "term_id",
    "term",
    "category",
    "why_flagged",
    "natural_option_id",
    "replacement_note",
    "added_at",
]

SEED_ADDITIVES = [
    ("A-001", "Maltodextrin", "Bulking agent",
     "Refined starch derivative, not a whole-food ingredient", "",
     "No direct clean-label equivalent; adjust solids with rice or millet flour."),
    ("A-002", "Monosodium glutamate", "Flavour enhancer",
     "Synthetic glutamate, not declarable in a clean-label product", "ING-017",
     "Toasted sesame carries savoury depth without an additive."),
    ("A-003", "Sodium benzoate", "Preservative",
     "Chemical preservative", "",
     "No clean-label equivalent; control moisture and water activity instead."),
    ("A-004", "Potassium sorbate", "Preservative",
     "Chemical preservative", "",
     "No clean-label equivalent; reach the shelf life by drying and packing."),
    ("A-005", "Hydrogenated vegetable fat", "Fat",
     "Partially hydrogenated fat carries trans-fat risk", "",
     "Use a declared cold-pressed oil or defatted groundnut flour."),
    ("A-006", "Artificial flavour", "Flavour",
     "Synthetic flavour blend, cannot be called natural", "",
     "Use whole spices or roasted flour notes and declare them."),
    ("A-007", "Tartrazine", "Colour",
     "Synthetic azo dye", "",
     "A whole-grain base usually needs no colour at all."),
    ("A-008", "Aspartame", "Sweetener",
     "Artificial sweetener", "ING-012",
     "Jaggery keeps the sweetening role, with sugar and colour."),
    ("A-009", "Xanthan gum", "Thickener",
     "Fermentation-derived additive", "ING-013",
     "Guar gum is a seed galactomannan already in the database."),
    ("A-010", "Carrageenan", "Thickener",
     "Seaweed extract flagged in clean-label audits", "ING-013",
     "Guar gum covers the same water-binding job."),
    ("A-011", "Sodium nitrite", "Preservative",
     "Curing salt, not appropriate for a shelf-stable snack", "",
     "Remove it rather than replace it."),
    ("A-012", "Vanillin", "Flavour",
     "Isolated synthetic vanillin", "",
     "Use whole vanilla if the flavour is needed, and declare it."),
]


def bootstrap() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not read_csv(ADDITIVES_CSV, ADDITIVE_FIELDS):
        write_csv(
            ADDITIVES_CSV,
            ADDITIVE_FIELDS,
            [row | {"added_at": now()} for row in (_as_dict(seed) for seed in SEED_ADDITIVES)],
        )


def _as_dict(seed: tuple) -> dict[str, str]:
    term_id, term, category, why_flagged, natural_option_id, replacement_note = seed
    return {
        "term_id": term_id,
        "term": term,
        "category": category,
        "why_flagged": why_flagged,
        "natural_option_id": natural_option_id,
        "replacement_note": replacement_note,
    }


def watchlist() -> list[dict[str, str]]:
    return read_csv(ADDITIVES_CSV, ADDITIVE_FIELDS)


def check(rows: list[dict]) -> list[dict]:
    """Check a formulation against the watchlist and each ingredient's clean-label flag.

    Returns one entry per ingredient that is flagged or needs confirmation:
    ``{ingredient, status, why, option, replacement_note}`` where status is ``flagged`` or
    ``review`` and ``option`` is the suggested replacement ingredient row (or None).
    """
    terms = watchlist()
    findings: list[dict] = []

    for row in rows:
        ingredient = row["ingredient"]
        declared = (ingredient["is_clean_label"] or "yes").strip().lower()
        haystack = f"{ingredient['name']} {ingredient['clean_label_note']}".lower()
        match = next((term for term in terms if term["term"].lower() in haystack), None)

        if match is not None:
            option = ingredients.get_ingredient(match["natural_option_id"]) if match["natural_option_id"] else None
            findings.append(
                {
                    "ingredient": ingredient,
                    "status": "flagged",
                    "why": f"{match['term']} — {match['category'].lower()}. {match['why_flagged']}.",
                    "option": option,
                    "replacement_note": match["replacement_note"],
                }
            )
        elif declared == "no":
            findings.append(
                {
                    "ingredient": ingredient,
                    "status": "flagged",
                    "why": ingredient["clean_label_note"] or "Marked not clean-label in the database.",
                    "option": None,
                    "replacement_note": "",
                }
            )
        elif declared == "check":
            findings.append(
                {
                    "ingredient": ingredient,
                    "status": "review",
                    "why": ingredient["clean_label_note"] or "Needs supplier confirmation.",
                    "option": None,
                    "replacement_note": "",
                }
            )

    return findings
