"""Formulations: storage, starter recipes, resolved blend models, and lab export."""

from __future__ import annotations

import auth
import ingredients
from storage import DATA_DIR, next_sequential_id, now, read_csv, write_csv

FORMULATIONS_CSV = DATA_DIR / "formulations.csv"
FORMULATION_ITEMS_CSV = DATA_DIR / "formulation_items.csv"

FORMULATION_FIELDS = [
    "formulation_id",
    "project_id",
    "name",
    "version",
    "created_by",
    "created_at",
    "notes",
]

FORMULATION_ITEM_FIELDS = [
    "formulation_id",
    "ingredient_id",
    "share_pct",
]

# Wheat-atta snack base the starter recipe is compared against. A reference recipe, not
# a market product: it is costed from the same ingredient table, so the comparison stays
# like-for-like.
BASELINE_ITEMS = [
    ("ING-011", 55.0),  # wheat flour
    ("ING-010", 25.0),  # rice flour
    ("ING-012", 15.0),  # jaggery
    ("ING-014", 3.0),   # iodised salt
    ("ING-013", 2.0),   # guar gum
]

STARTER_ITEMS = [
    ("ING-001", 42.0),  # pearl millet flour
    ("ING-005", 26.0),  # defatted soy flour
    ("ING-010", 18.0),  # rice flour
    ("ING-012", 10.0),  # jaggery
    ("ING-013", 2.5),   # guar gum
    ("ING-014", 1.5),   # iodised salt
]


def bootstrap() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not FORMULATIONS_CSV.exists():
        write_csv(FORMULATIONS_CSV, FORMULATION_FIELDS, [])
    if not FORMULATION_ITEMS_CSV.exists():
        write_csv(FORMULATION_ITEMS_CSV, FORMULATION_ITEM_FIELDS, [])


def resolve(items: list[tuple[str, float]]) -> list[dict]:
    """Join recipe items (ingredient id, share %) to the ingredient database, in order."""
    rows = []
    for ingredient_id, share_pct in items:
        ingredient = ingredients.get_ingredient(ingredient_id)
        if ingredient is None:
            continue
        rows.append({"ingredient": ingredient, "share_pct": share_pct})
    return rows


def starter_items() -> list[tuple[str, float]]:
    """The starter recipe as editable (ingredient id, share %) pairs."""
    return list(STARTER_ITEMS)


def starter_formulation() -> list[dict]:
    return resolve(STARTER_ITEMS)


def reference_base() -> list[dict]:
    """The plain wheat-atta snack the starter recipe is compared with."""
    return resolve(BASELINE_ITEMS)


def total_share(rows: list[dict]) -> float:
    return round(sum(row["share_pct"] for row in rows), 1)


def get_latest_project_formulation(project_id: str) -> tuple[dict[str, str] | None, list[tuple[str, float]]]:
    """Return the most recently saved formulation metadata and items for this project.

    If no saved formulation exists yet, returns (None, starter_items()).
    """
    all_formulations = read_csv(FORMULATIONS_CSV, FORMULATION_FIELDS)
    project_forms = [f for f in all_formulations if f["project_id"] == project_id]
    if not project_forms:
        return None, starter_items()

    # Newest version first
    project_forms.sort(key=lambda f: (int(f.get("version") or 1), f.get("created_at") or ""), reverse=True)
    latest = project_forms[0]

    all_items = read_csv(FORMULATION_ITEMS_CSV, FORMULATION_ITEM_FIELDS)
    matching_items = [
        (item["ingredient_id"], float(item["share_pct"]))
        for item in all_items
        if item["formulation_id"] == latest["formulation_id"]
    ]

    if not matching_items:
        return latest, starter_items()

    return latest, matching_items


def save_project_formulation(
    project_id: str,
    items: list[tuple[str, float]],
    user_id: str,
    name: str = "",
    notes: str = "",
) -> tuple[bool, str, str]:
    """Persist a candidate formulation for this project to CSV."""
    if not items:
        return False, "Cannot save an empty formulation.", ""

    total = round(sum(share for _, share in items), 1)
    if abs(total - 100.0) > 0.5:
        return False, f"Ingredient shares must sum to 100% (currently {total}%).", ""

    all_formulations = read_csv(FORMULATIONS_CSV, FORMULATION_FIELDS)
    project_forms = [f for f in all_formulations if f["project_id"] == project_id]
    version = max([int(f.get("version") or 0) for f in project_forms], default=0) + 1

    formulation_id = next_sequential_id("F", all_formulations, "formulation_id")
    formulation_record = {
        "formulation_id": formulation_id,
        "project_id": project_id,
        "name": name or f"Formulation v{version}",
        "version": str(version),
        "created_by": user_id,
        "created_at": now(),
        "notes": notes,
    }

    all_formulations.append(formulation_record)
    write_csv(FORMULATIONS_CSV, FORMULATION_FIELDS, all_formulations)

    all_items = read_csv(FORMULATION_ITEMS_CSV, FORMULATION_ITEM_FIELDS)
    for ingredient_id, share in items:
        all_items.append(
            {
                "formulation_id": formulation_id,
                "ingredient_id": ingredient_id,
                "share_pct": f"{share:.1f}",
            }
        )
    write_csv(FORMULATION_ITEMS_CSV, FORMULATION_ITEM_FIELDS, all_items)

    auth.log_event(
        user_id,
        table="formulations",
        record_id=formulation_id,
        new_value=f"v{version} ({len(items)} items)",
        note=f"Saved formulation for project {project_id}",
    )

    return True, f"Saved Formulation v{version} successfully.", formulation_id


def build_lab_spec_sheet(
    project: dict[str, str],
    recipe_rows: list[dict],
    blend_nutrition: dict[str, float],
    blend_cost: float,
    baseline_cost: float,
    serving_cost: float,
    findings: list[dict],
    formulation_meta: dict[str, str] | None = None,
) -> str:
    """Generate a clean, printable Markdown Lab Validation Spec Sheet."""
    version_str = f"v{formulation_meta.get('version', '1')}" if formulation_meta else "Draft (Unsaved)"
    formulation_id = formulation_meta.get("formulation_id", "F-DRAFT") if formulation_meta else "F-DRAFT"

    delta_pct = (blend_cost - baseline_cost) / baseline_cost * 100 if baseline_cost else 0.0
    delta_sign = "+" if delta_pct > 0 else ""

    lines = [
        "# SMARTCROP.AI — LAB VALIDATION SPEC SHEET",
        "",
        "> **IMPORTANT R&D NOTICE**: This formulation is an AI-assisted computational starting point. "
        "It must undergo laboratory verification, food-safety screening, microbiological evaluation, "
        "and sensory panel testing before commercialization or human consumption.",
        "",
        "## 1. Project & Batch Metadata",
        f"- **Project Name**: {project.get('name', 'Untitled')}",
        f"- **Project ID**: {project.get('project_id', '')}",
        f"- **Formulation ID**: {formulation_id} ({version_str})",
        f"- **Lab Name**: {auth.LAB_NAME} ({project.get('lab_id', '')})",
        f"- **Generated At**: {now()}",
        f"- **Description / Goal**: {project.get('description', 'Clean-label plant-based formulation')}",
        "",
        "## 2. Target Formulation Composition (per 100 g batch)",
        "| Ingredient | Local / Regional Name | Category | Share (%) | Cost (₹/100g) | Data Confidence |",
        "| :--- | :--- | :--- | :---: | :---: | :---: |",
    ]

    for row in recipe_rows:
        ing = row["ingredient"]
        local = ing.get("local_name") or "-"
        cat = ing.get("category") or "-"
        price = ingredients.cost_per_100g(ing)
        conf = ing.get("nutrition_confidence") or "unknown"
        lines.append(f"| {ing['name']} | {local} | {cat} | {row['share_pct']:.1f}% | ₹{price:,.2f} | {conf} |")

    lines.extend([
        "",
        "## 3. Nutritional Profile (Computed per 100 g blend)",
        f"- **Energy**: {blend_nutrition.get('energy_kcal', 0):.0f} kcal",
        f"- **Protein**: {blend_nutrition.get('protein_g', 0):.1f} g",
        f"- **Fat**: {blend_nutrition.get('fat_g', 0):.1f} g",
        f"- **Total Carbohydrates**: {blend_nutrition.get('carbs_g', 0):.1f} g",
        f"- **Dietary Fibre**: {blend_nutrition.get('fibre_g', 0):.1f} g",
        "",
        "## 4. Cost & Commercial Feasibility (Mandi Spot Basis)",
        f"- **Ingredient Cost per kg**: ₹{blend_cost:,.2f} / kg",
        f"- **Cost per 40 g Serving**: ₹{serving_cost:,.2f}",
        f"- **Reference Base Cost (Wheat-Atta Snack)**: ₹{baseline_cost:,.2f} / kg",
        f"- **Economic Variance**: {delta_sign}{delta_pct:.1f}% vs reference base",
        "",
        "## 5. Clean-Label & Additive Status",
    ])

    flagged = [f for f in findings if f["status"] == "flagged"]
    review = [f for f in findings if f["status"] == "review"]

    if not findings:
        lines.append("- **Verdict**: 100% CLEAN-LABEL COMPLIANT (Zero synthetic additives detected from watchlist).")
    else:
        if flagged:
            lines.append(f"- **Flagged Synthetic Additives ({len(flagged)})**:")
            for item in flagged:
                lines.append(f"  - `{item['ingredient']['name']}`: {item['why']}")
                if item.get("option"):
                    lines.append(f"    * Recommended Natural Substitute: {item['option']['name']} (₹{ingredients.cost_per_100g(item['option']):,.2f}/100g)")
        if review:
            lines.append(f"- **Ingredients Requiring Supplier Confirmation ({len(review)})**:")
            for item in review:
                lines.append(f"  - `{item['ingredient']['name']}`: {item['why']}")

    lines.extend([
        "",
        "## 6. Lab Sign-Off & Verification Signatures",
        "- [ ] Sensory / Texture evaluation completed",
        "- [ ] Proximate analysis (Moisture, Protein, Fat, Ash) verified in lab",
        "- [ ] Water activity ($a_w$) and shelf-life verified",
        "- [ ] FSSAI / regulatory standard verified",
        "",
        "**Formulated by**: _______________________      **Date**: _____________",
        "",
        "**Lab Admin / Sign-Off**: _________________      **Date**: _____________",
        "",
        "---",
        "*SmartCrop.AI — Developed for HIMOVATION 2026 Solve-a-Thon by Panchayat of Programmers*",
    ])

    return "\n".join(lines)
