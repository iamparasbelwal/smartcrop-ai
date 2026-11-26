"""Indian regional sourcing affinity & landed cost estimation for SmartCrop.AI."""

from __future__ import annotations

import re

import ingredients

TARGET_REGIONS = (
    "Pan-India",
    "Rajasthan",
    "Karnataka",
    "Maharashtra",
    "Madhya Pradesh",
    "Gujarat",
    "Andhra Pradesh",
    "Punjab",
    "West Bengal",
    "Uttarakhand",
)

# Text aliases matched against project descriptions or user chat instructions
REGION_ALIASES: dict[str, tuple[str, ...]] = {
    "Rajasthan": ("rajasthan", "jaipur", "jodhpur", "bikaner", "marwar", "nagaur"),
    "Karnataka": ("karnataka", "bengaluru", "bangalore", "mysuru", "mysore"),
    "Maharashtra": ("maharashtra", "pune", "mumbai", "nagpur", "solapur", "kolhapur", "marathwada"),
    "Madhya Pradesh": ("madhya pradesh", "indore", "bhopal", "malwa", "ujjain"),
    "Gujarat": ("gujarat", "ahmedabad", "surat", "saurashtra", "anand", "kutch"),
    "Andhra Pradesh": ("andhra pradesh", "andhra", "telangana", "hyderabad", "vijayawada", "guntur"),
    "Punjab": ("punjab", "haryana", "ludhiana", "chandigarh"),
    "West Bengal": ("west bengal", "bengal", "kolkata", "odisha", "bihar"),
    "Uttarakhand": ("uttarakhand", "dehradun", "garhwal", "kumaon", "himalayan"),
}

# Neighboring / adjacent procurement corridors for Tier 2 sourcing
NEIGHBORS: dict[str, set[str]] = {
    "Rajasthan": {"Gujarat", "Madhya Pradesh", "Punjab", "Maharashtra"},
    "Karnataka": {"Maharashtra", "Andhra Pradesh"},
    "Maharashtra": {"Gujarat", "Madhya Pradesh", "Karnataka", "Andhra Pradesh"},
    "Madhya Pradesh": {"Rajasthan", "Gujarat", "Maharashtra"},
    "Gujarat": {"Rajasthan", "Maharashtra", "Madhya Pradesh"},
    "Andhra Pradesh": {"Karnataka", "Maharashtra", "West Bengal"},
    "Punjab": {"Rajasthan", "Uttarakhand", "Madhya Pradesh"},
    "West Bengal": {"Andhra Pradesh"},
    "Uttarakhand": {"Punjab", "Rajasthan", "Madhya Pradesh"},
}

FREIGHT_LOCAL = 0.0
FREIGHT_NEARBY = 3.5
FREIGHT_DISTANT = 9.0


def normalize_region(region: str | None) -> str:
    raw = (region or "").strip()
    if not raw or raw.lower() == "pan-india":
        return "Pan-India"
    low = raw.lower()
    for canonical in TARGET_REGIONS:
        if canonical.lower() == low:
            return canonical
    for canonical, aliases in REGION_ALIASES.items():
        if any(re.search(rf"\b{re.escape(alias)}\b", low) for alias in aliases):
            return canonical
    return raw


def detect_target_region(
    instruction: str = "",
    *,
    explicit_region: str = "",
    project_text: str = "",
) -> str:
    """Resolve target Indian market region: chat mention overrides project default if specified."""
    for source in (instruction, project_text):
        low = (source or "").lower()
        if not low:
            continue
        for canonical, aliases in REGION_ALIASES.items():
            if any(re.search(rf"\b{re.escape(alias)}\b", low) for alias in aliases):
                return canonical
    exp = normalize_region(explicit_region)
    return exp if exp else "Pan-India"


def score_ingredient_region(crop_region: str, target_region: str) -> tuple[str, float]:
    """Return (tier_code, freight_surcharge_rs_per_kg) for one crop relative to target region.

    tier_code is one of: 'LOCAL', 'NEARBY', 'DISTANT', 'STANDARD'.
    """
    target = normalize_region(target_region)
    if not target or target == "Pan-India":
        return "STANDARD", 0.0
    crop_norm = normalize_region(crop_region)
    if crop_norm.lower() == target.lower():
        return "LOCAL", FREIGHT_LOCAL
    if crop_norm in NEIGHBORS.get(target, set()):
        return "NEARBY", FREIGHT_NEARBY
    return "DISTANT", FREIGHT_DISTANT


def effective_cost_per_kg(ingredient_row: dict, target_region: str) -> tuple[float, str, float]:
    """Return (landed_cost_per_kg, tier_code, freight_surcharge) for ranking & costing."""
    base = ingredients.number(ingredient_row, "cost_per_kg")
    tier, freight = score_ingredient_region(str(ingredient_row.get("region") or ""), target_region)
    return round(base + freight, 2), tier, freight


def evaluate_blend(resolved_rows: list[dict], target_region: str) -> dict:
    """Compute regional sourcing metrics and estimated landed cost breakdown."""
    target = normalize_region(target_region)
    if not resolved_rows:
        return {
            "target_region": target,
            "is_targeted": target != "Pan-India",
            "mandi_cost_per_kg": 0.0,
            "freight_per_kg": 0.0,
            "landed_cost_per_kg": 0.0,
            "local_share_pct": 0.0,
            "tier1_share_pct": 0.0,
            "savings_vs_distant": 0.0,
        }

    mandi_total = 0.0
    freight_total = 0.0
    local_share = 0.0
    tier1_share = 0.0

    for r in resolved_rows:
        ing = r["ingredient"]
        share = float(r.get("share_pct") or 0.0)
        base_cost = ingredients.number(ing, "cost_per_kg")
        tier, freight = score_ingredient_region(str(ing.get("region") or ""), target)
        mandi_total += base_cost * share / 100.0
        freight_total += freight * share / 100.0
        if tier in ("LOCAL", "NEARBY"):
            local_share += share
        if tier == "LOCAL":
            tier1_share += share

    landed = mandi_total + freight_total
    savings = max(0.0, FREIGHT_DISTANT - freight_total) if target != "Pan-India" else 0.0
    return {
        "target_region": target,
        "is_targeted": target != "Pan-India",
        "mandi_cost_per_kg": round(mandi_total, 2),
        "freight_per_kg": round(freight_total, 2),
        "landed_cost_per_kg": round(landed, 2),
        "local_share_pct": round(local_share, 1),
        "tier1_share_pct": round(tier1_share, 1),
        "savings_vs_distant": round(savings, 2),
    }
