"""Check model answers against the SmartCrop skill, using the app's own database and validator.

Run from the project folder (the one that holds app.py):

    py ai_skill/tests/check_blend.py                      # checks reference_answers.json
    py ai_skill/tests/check_blend.py my_model_answers.json

An answers file looks like reference_answers.json: {"answers": {"<turn id>": {reasoning,
selected_notes, reply, recipe}}}. Paste a real model's JSON under each turn id to test it.
Prints one line per check and exits with code 1 if any hard check fails.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))  # project root, so the app's modules import

import formulations  # noqa: E402
import ingredients  # noqa: E402
import nutrition  # noqa: E402

FIGURES = re.compile(r"(₹|\brs\.?)\s*\d|\d\s*(kcal|calories|grams|g\b|rupees|/kg)", re.IGNORECASE)
MARKDOWN = re.compile(r"(\*\*|__|`|^\s*[-*•]\s|^#{1,6}\s)", re.MULTILINE)
EMOJI = re.compile("[\U0001F300-\U0001FAFF\u2600-\u27BF]")
ING_ID = re.compile(r"\bING-\d+\b")


def pairs(recipe: list[dict]) -> list[tuple[str, float]]:
    return [(str(r["ingredient_id"]), float(r["share_pct"])) for r in recipe]


def blend(items):
    rows = formulations.resolve(items)
    return nutrition.blend_nutrition(rows), nutrition.cost_per_kg(rows), rows


def run(answers_path: Path) -> int:
    spec = json.loads((HERE / "test_prompts.json").read_text(encoding="utf-8"))
    answers = json.loads(answers_path.read_text(encoding="utf-8"))["answers"]
    fails = warns = total = 0

    def report(label: str, ok: bool, detail: str = "", soft: bool = False) -> None:
        nonlocal fails, warns, total
        total += 1
        mark = "pass" if ok else ("warn" if soft else "FAIL")
        if not ok:
            warns += soft
            fails += not soft
        print(f"  [{mark}] {label}" + (f" - {detail}" if detail and not ok else ""))

    for scenario in spec["scenarios"]:
        previous: list[tuple[str, float]] = []
        print(f"\nScenario {scenario['id']}: {scenario['project_name']}")
        for turn in scenario["turns"]:
            print(f"\n {turn['id']}  ({turn['turn']}): {turn['prompt']}")
            ans = answers.get(turn["id"])
            if ans is None:
                report("answer present", False, "no answer for this turn id")
                continue
            expect = turn["expect"]
            items = pairs(ans.get("recipe") or [])
            reply, reasoning = ans.get("reply", ""), ans.get("reasoning", "")
            notes_text = f"{ans.get('selected_notes', '')} {reply} {reasoning}"

            report("reasoning names the turn type", turn["turn"].lower() in reasoning.lower())
            report("reply 95 words or fewer", len(reply.split()) <= 95, f"{len(reply.split())} words")
            report("reasoning 150 words or fewer", len(reasoning.split()) <= 150, f"{len(reasoning.split())} words", soft=True)
            report("reply has no ING- ids", not ING_ID.search(reply))
            report("reply has no markdown or emoji", not (MARKDOWN.search(reply) or EMOJI.search(reply)))
            report("reply states no nutrition or cost figures", not FIGURES.search(reply), FIGURES.search(reply).group(0) if FIGURES.search(reply) else "")

            if expect.get("empty_recipe"):
                report("recipe is empty for a question", not items)
            else:
                report("reply says starting point / lab validation", "lab" in reply.lower() and "validat" in reply.lower())
                ok, validated, corrections = formulations.validate_items(items)
                report("every id exists in the database", all(ingredients.get_ingredient(i) for i, _ in items))
                report("passes the app's gate with no silent corrections", ok and not corrections, "; ".join(corrections))
                report("4-7 crops", 4 <= len(items) <= 7, f"{len(items)} crops", soft=True)
                if ok:
                    _, _, rows = blend(items)
                    cats = {r["ingredient"]["category"] for r in rows}
                    ids = {r["ingredient"]["ingredient_id"] for r in rows}
                    flags = {(r["ingredient"]["is_clean_label"] or "yes").lower() for r in rows}
                    if expect.get("forbid_ids"):
                        bad = ids & set(expect["forbid_ids"])
                        report("no forbidden ingredients", not bad, ", ".join(sorted(bad)))
                    if expect.get("require_ids"):
                        missing = set(expect["require_ids"]) - ids
                        report("has required ingredients", not missing, ", ".join(sorted(missing)))
                    if expect.get("forbid_categories"):
                        bad = cats & set(expect["forbid_categories"])
                        report("no forbidden categories", not bad, ", ".join(sorted(bad)))
                    if expect.get("forbid_clean_label"):
                        bad = flags & set(expect["forbid_clean_label"])
                        report("honours clean-label", not bad, ", ".join(sorted(bad)))
                    if expect.get("require_categories_any"):
                        report("has a protein-role crop", bool(cats & set(expect["require_categories_any"])))
                    if previous:
                        before = {i for i, _ in previous}
                        removed = before - ids
                        if "min_removed_vs_previous" in expect:
                            report("rebuilt from scratch (old crops dropped)", len(removed) >= expect["min_removed_vs_previous"], f"only {len(removed)} dropped")
                        if expect.get("same_as_previous"):
                            report("blend returned unchanged", validated == [(k, round(v, 1)) for k, v in previous])
                        if expect.get("cheaper_than_previous") or "protein_not_below_previous_by" in expect:
                            old_n, old_c, _ = blend(previous)
                            new_n, new_c, _ = blend(items)
                            if expect.get("cheaper_than_previous"):
                                report("cost went down", new_c < old_c, f"{old_c:.1f} -> {new_c:.1f} Rs/kg")
                            if "protein_not_below_previous_by" in expect:
                                slack = expect["protein_not_below_previous_by"]
                                report("protein held", new_n["protein_g"] >= old_n["protein_g"] - slack, f"{old_n['protein_g']} -> {new_n['protein_g']} g")
                if items:
                    previous = [(k, v) for k, v in items]
            if expect.get("text_mentions_any"):
                words = expect["text_mentions_any"]
                report("mentions " + " / ".join(words), any(w.lower() in notes_text.lower() for w in words))

    print(f"\n{total - fails - warns}/{total} checks passed, {warns} warnings, {fails} failures")
    return 1 if fails else 0


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "reference_answers.json"
    sys.exit(run(target))
