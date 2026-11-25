"""The only place SmartCrop.AI talks to Google Gemini.

Ground rules, kept here so they cannot drift into a page:

* The model **never does arithmetic**. It reads the crop catalog and the recipe, proposes
  ingredient shares or explains a trade-off; `nutrition.py` computes every figure and
  `formulations.validate_items` is the gate every proposal must pass (real ids, shares total
  100 %, each crop under its practical cap).
* The key lives in `.env` only. Nothing here prints it or hands it to the browser.
* If the key is missing or Google is unreachable, `GeminiError` is raised and the callers fall
  back to the local rules in `whatif.py`, so the demo never dead-ends.

Plain `urllib` only — no SDK, no extra wheel to install on Python 3.14.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

import ingredients
import nutrition

APP_DIR = Path(__file__).resolve().parent
ENV_FILE = APP_DIR / ".env"
API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"

# Tried in order. Native thinking models run first when healthy; flash-lite-latest provides fast
# structured chain-of-thought fallback if Google returns 503/timeout on larger models.
FALLBACK_MODELS = (
    "gemini-flash-latest",
    "gemini-flash-lite-latest",
    "gemini-3.1-flash-lite",
    "gemini-3.1-flash-lite-preview",
    "gemini-pro-latest",
    "gemini-3-flash-preview",
)
TIMEOUT_SECONDS = 18
MAX_WORDS = 95

SYSTEM_RULES = (
    "You are the SmartCrop.AI food-R&D formulation co-pilot inside a private research lab's web app. "
    "Before proposing a blend, carefully analyze the project goal, product format (biscuit, pasta, "
    "flatbread, extruded snack, khoya/dairy substitute, porridge, bar, etc.), nutrition/cost targets, "
    "clean-label requirements, and every row in the private crop & ingredient database. "
    "Hard rules: (1) All numeric nutrition and cost calculations are done by Python — never invent or "
    "state final calories, protein, fat, carbs, fibre, or Rs/kg figures in your reply text; the app "
    "computes and appends exact verified numbers. (2) Only use ingredient_ids that exist in the private "
    "database you are given. (3) Shares are percentages totaling 100 and each crop must stay at or below "
    "its max practical percent. (4) Respect clean-label requests strictly: when the user asks for "
    "clean label, minimum additives, or zero additives, exclude ingredients flagged is_clean_label='check' "
    "(such as hexane-extracted Defatted soy flour) unless explicitly requested, and avoid unnecessary gums. "
    "(5) Match ingredients to the culinary/processing form (e.g. don't put jaggery in savory pasta; adapt "
    "binders, flours, legumes, and oilseeds appropriately). (6) In `reply`, write plain conversational "
    "sentences (<= "
    f"{MAX_WORDS} words, no markdown, no bullets, no emojis, no ingredient IDs like ING-001). "
    "(7) Mention once that the blend is a starting point needing lab validation."
)

RECIPE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "reasoning": {"type": "STRING"},
        "selected_notes": {"type": "STRING"},
        "reply": {"type": "STRING"},
        "recipe": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "ingredient_id": {"type": "STRING"},
                    "share_pct": {"type": "NUMBER"},
                },
                "required": ["ingredient_id", "share_pct"],
            },
        },
    },
    "required": ["reasoning", "selected_notes", "reply", "recipe"],
}

DRAFT_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "name": {"type": "STRING"},
        "rationale": {"type": "STRING"},
        "recipe": RECIPE_SCHEMA["properties"]["recipe"],
    },
    "required": ["name", "rationale", "recipe"],
}


class GeminiError(RuntimeError):
    """A model call that did not produce a usable answer."""

    def __init__(self, message: str, retryable: bool = False) -> None:
        super().__init__(message)
        self.retryable = retryable


# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #
_config: dict[str, object] = {}


def _load_config() -> dict[str, object]:
    """Read `.env` once per process: the key and the model preference."""
    key = (os.environ.get("GEMINI_API_KEY") or "").strip()
    preferred = (os.environ.get("GEMINI_MODEL") or "").strip()

    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            name, _, value = line.partition("=")
            value = value.strip().strip('"').strip("'")
            if name.strip() == "GEMINI_API_KEY" and not key:
                key = value
            elif name.strip() == "GEMINI_MODEL" and not preferred:
                preferred = value

    models: list[str] = []
    for model in (preferred, *FALLBACK_MODELS):
        if model and model not in models:
            models.append(model)
    return {"key": key, "models": models}


def config() -> dict[str, object]:
    if not _config:
        _config.update(_load_config())
    return _config


def reload_config() -> None:
    """Pick up a key added to `.env` while the app is running."""
    _config.clear()
    config()


def available() -> bool:
    return bool(config()["key"])


def model_name() -> str:
    """The model that answered last, or the first preference when nothing has run yet."""
    return str(_config.get("last_model") or (config()["models"] or ["gemini"])[0])


def status_label() -> str:
    return f"Gemini · {model_name()}" if available() else "Local rules (no key)"


# --------------------------------------------------------------------------- #
# Transport
# --------------------------------------------------------------------------- #
def _http_message(code: int, body: str) -> tuple[str, bool]:
    snippet = ""
    try:
        snippet = (json.loads(body).get("error") or {}).get("message") or ""
    except (ValueError, AttributeError):
        snippet = body[:160]
    if code in (400, 401, 403):
        if any(word in snippet.upper() for word in ("API KEY", "API_KEY", "PERMISSION", "CREDENTIAL")):
            return ("The Gemini key was rejected. Check GEMINI_API_KEY in the .env file.", False)
        return (f"Gemini rejected the request: {snippet}"[:240], False)
    if code == 404:
        return (f"Gemini does not offer this model to this key. {snippet}"[:220], True)
    if code == 429:
        return ("Gemini's free quota is busy right now. Try again in a minute.", True)
    if code in (500, 502, 503, 504):
        return ("Gemini is under heavy load right now. Try again in a moment.", True)
    return (f"Gemini returned HTTP {code}. {snippet}"[:220], False)


def _post(model: str, payload: dict) -> dict:
    url = f"{API_BASE}/{model}:generateContent?key={config()['key']}"
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        message, retryable = _http_message(exc.code, exc.read().decode("utf-8", "replace"))
        raise GeminiError(message, retryable) from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        reason = getattr(exc, "reason", exc)
        raise GeminiError(f"Could not reach Gemini ({reason}).", True) from exc


def _text_of(data: dict) -> str:
    candidates = data.get("candidates") or []
    if not candidates:
        feedback = (data.get("promptFeedback") or {}).get("blockReason")
        raise GeminiError(f"Gemini refused this prompt{': ' + feedback if feedback else '.'}", False)
    parts = (candidates[0].get("content") or {}).get("parts") or []
    text = "".join(part.get("text") or "" for part in parts).strip()
    if not text:
        finish = candidates[0].get("finishReason") or "no text"
        raise GeminiError(f"Gemini returned an empty answer ({finish}).", True)
    return text


def _generate(
    prompt: str,
    *,
    system: str = SYSTEM_RULES,
    schema: dict | None = None,
    temperature: float = 0.4,
    max_tokens: int = 900,
) -> str:
    """One prompt, walked through the model list until one answers."""
    if not available():
        raise GeminiError("No Gemini key is configured.")

    base_payload: dict = {
        "systemInstruction": {"parts": [{"text": system}]},
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": max_tokens,
        },
    }
    if schema is not None:
        base_payload["generationConfig"]["responseMimeType"] = "application/json"
        base_payload["generationConfig"]["responseSchema"] = schema

    last_error: GeminiError | None = None
    candidates = list(config()["models"])
    dead_models: set[str] = set()

    for attempt in range(2):
        if attempt > 0:
            time.sleep(1.5)
        for model in candidates:
            if model in dead_models:
                continue
            payload = json.loads(json.dumps(base_payload))
            if "lite" not in model.lower():
                # Give thinking-capable models real thinking budget so they reason carefully before output.
                payload["generationConfig"]["thinkingConfig"] = {"thinkingBudget": 1024}
                payload["generationConfig"]["maxOutputTokens"] = max(max_tokens, 2600)
            try:
                data = _post(model, payload)
            except GeminiError as exc:
                if "quota" in str(exc).lower() or "no longer available" in str(exc).lower():
                    dead_models.add(model)
                if exc.retryable:
                    last_error = exc
                    continue
                if "key" in str(exc).lower() and "rejected" in str(exc).lower():
                    raise
                if "thinkingConfig" not in payload["generationConfig"]:
                    last_error = exc
                    continue
                # Models that reject thinkingConfig with 400 INVALID_ARGUMENT still have to answer.
                plain = json.loads(json.dumps(base_payload))
                plain["generationConfig"]["maxOutputTokens"] = max(max_tokens, 2000)
                try:
                    data = _post(model, plain)
                except GeminiError as retry_error:
                    last_error = retry_error
                    continue

            finish = ((data.get("candidates") or [{}])[0]).get("finishReason") or ""
            if finish == "MAX_TOKENS":
                last_error = GeminiError("Gemini ran out of room mid-answer.", True)
                continue
            _config["last_model"] = model
            return _text_of(data)

    raise last_error or GeminiError("Gemini did not answer.")


def _json_of(text: str) -> dict:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("```")[1] if "```" in cleaned[3:] else cleaned[3:]
        cleaned = cleaned.removeprefix("json").strip()
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start == -1 or end == -1:
        raise GeminiError("Gemini's answer was not readable.", True)
    try:
        payload = json.loads(cleaned[start : end + 1])
    except ValueError as exc:
        raise GeminiError("Gemini's answer was not readable.", True) from exc
    if not isinstance(payload, dict):
        raise GeminiError("Gemini's answer was not readable.", True)
    return payload


# --------------------------------------------------------------------------- #
# Prompt material
# --------------------------------------------------------------------------- #
def catalog_text() -> str:
    """The private crop & ingredient database as compact lines the model can reason over."""
    lines = []
    for row in ingredients.list_ingredients():
        local = row.get("local_name") or "-"
        region = row.get("region") or "-"
        note = row.get("clean_label_note") or "-"
        nut_conf = row.get("nutrition_confidence") or "estimated"
        cost_conf = row.get("cost_confidence") or "estimated"
        lines.append(
            " | ".join(
                [
                    row["ingredient_id"],
                    row["name"],
                    local,
                    row.get("category") or "Crop",
                    region,
                    f"energy {ingredients.number(row, 'energy_kcal'):.0f} kcal",
                    f"protein {ingredients.number(row, 'protein_g'):.1f} g",
                    f"fat {ingredients.number(row, 'fat_g'):.1f} g",
                    f"carbs {ingredients.number(row, 'carbs_g'):.1f} g",
                    f"fibre {ingredients.number(row, 'fibre_g'):.1f} g",
                    f"cost Rs {ingredients.number(row, 'cost_per_kg'):.0f}/kg",
                    f"max {ingredients.number(row, 'max_practical_pct'):.0f}%",
                    f"clean-label {row.get('is_clean_label') or 'yes'} ({note})",
                    f"confidence nut={nut_conf}/cost={cost_conf}",
                ]
            )
        )
    return "\n".join(lines)


def recipe_text(recipe_rows: list[dict]) -> str:
    return "\n".join(
        f"{row['ingredient']['ingredient_id']} {row['ingredient']['name']} {row['share_pct']:.1f}%"
        for row in recipe_rows
    )


# --------------------------------------------------------------------------- #
# Public calls
# --------------------------------------------------------------------------- #
def discuss(
    instruction: str,
    recipe_rows: list[dict],
    *,
    project_name: str = "",
    project_description: str = "",
    db_brief: str = "",
    history: list[dict] | None = None,
) -> dict:
    """Answer one chat instruction with explicit DB reasoning and optional recipe.

    Returns ``{"reply": str, "reasoning": str, "selected_notes": str, "recipe": [(id, share), ...] | None}``.
    """
    recent = ""
    if history:
        recent_lines = [
            f"{'User' if message['role'] == 'user' else 'You'}: {message['text']}"
            for message in history[-6:]
        ]
        recent = "Recent conversation:\n" + "\n".join(recent_lines) + "\n\n"

    if recipe_rows:
        current_block = f"Current recipe (percent of the blend):\n{recipe_text(recipe_rows)}\n\n"
        task_block = (
            "1. In `reasoning`, analyze what the user wants, compare candidate crops from the private "
            "database (protein, cost, region, product format, clean-label check flags), and explain trade-offs.\n"
            "2. In `selected_notes`, note which ingredients you kept, added, or excluded (especially flagged/check items).\n"
            "3. Decide whether this requires changing the blend or just answering a question. "
            "If changing the blend, return the COMPLETE updated recipe in `recipe` (all remaining ingredients "
            "summing to 100%, each under max practical cap). If purely a question, return an empty list."
        )
    else:
        current_block = "Current recipe: None yet (empty project — build from the private database).\n\n"
        task_block = (
            "No formulation exists yet.\n"
            "1. In `reasoning`, carefully analyze the product format/type requested, regional or processing goals, "
            "and compare protein/energy/cost/clean-label status across the crops in the private database.\n"
            "2. In `selected_notes`, state why you selected specific ING-xxx crops (and excluded incompatible or "
            "flagged items such as hexane-extracted ING-005 when clean-label/minimum additives is desired).\n"
            "3. In `recipe`, construct ONE complete starting formulation (4–7 database ingredients summing to 100%, "
            "each strictly <= max_practical_pct) tailored to this project. Only return an empty list if the user "
            "is purely asking an informational question."
        )

    desc_line = f"Project description: {project_description.strip()}\n" if project_description.strip() else ""
    brief_line = f"Pre-screened DB findings:\n{db_brief.strip()}\n\n" if db_brief.strip() else ""
    prompt = (
        f"Project end goal: {project_name or 'untitled formulation'}.\n"
        f"{desc_line}"
        f"Private lab crop & ingredient database (id | name | local_name | category | region | "
        f"composition per 100 g | cost | cap | clean-label | confidence):\n"
        f"{catalog_text()}\n\n"
        f"{brief_line}"
        f"{current_block}"
        f"{recent}"
        f"The user says: {instruction.strip()}\n\n"
        f"{task_block}"
    )
    payload = _json_of(_generate(prompt, schema=RECIPE_SCHEMA, max_tokens=1600))
    reply = str(payload.get("reply") or "").strip()
    reasoning = str(payload.get("reasoning") or "").strip()
    selected_notes = str(payload.get("selected_notes") or "").strip()

    recipe: list[tuple[str, float]] | None = None
    raw = payload.get("recipe") or []
    if isinstance(raw, list) and raw:
        pairs: list[tuple[str, float]] = []
        for item in raw:
            if not isinstance(item, dict):
                continue
            try:
                pairs.append((str(item.get("ingredient_id") or ""), float(item.get("share_pct") or 0)))
            except (TypeError, ValueError):
                continue
        recipe = pairs or None

    if not reply:
        reply = "I could not put that into words — try rephrasing the instruction."
    return {
        "reply": reply,
        "reasoning": reasoning,
        "selected_notes": selected_notes,
        "recipe": recipe,
    }


def draft(brief: str, *, project_name: str = "", cook: str = "") -> dict:
    """Propose a fresh formulation from a plain-language brief.

    Returns ``{"name", "rationale", "recipe": [(id, share)]}``; the page validates the recipe
    before it is allowed into the workbench.
    """
    prompt = (
        f"Project: {project_name or 'a new snack'}.\n"
        f"The lab asks for: {brief.strip()}\n"
        + (f"Processing note: {cook.strip()}\n" if cook.strip() else "")
        + f"\nCrop catalog (id | name | category | composition per 100 g | cost | cap | clean-label):\n"
        f"{catalog_text()}\n\n"
        "Build one practical starting recipe from this catalog only. Respect every crop's cap, "
        "keep the ingredient list to 4–7 crops, and make the shares total 100. "
        "Give it a short product name (two to four words) and a rationale of at most 60 plain words."
    )
    payload = _json_of(_generate(prompt, schema=DRAFT_SCHEMA, temperature=0.5))

    pairs: list[tuple[str, float]] = []
    for item in payload.get("recipe") or []:
        if not isinstance(item, dict):
            continue
        try:
            pairs.append((str(item.get("ingredient_id") or ""), float(item.get("share_pct") or 0)))
        except (TypeError, ValueError):
            continue

    return {
        "name": str(payload.get("name") or "AI draft").strip()[:60],
        "rationale": str(payload.get("rationale") or "").strip(),
        "recipe": pairs,
    }


def explain_blend(recipe_rows: list[dict], blend: dict[str, float], cost: float) -> str:
    """A short, plain-language read of a blend. The figures are handed in, never guessed."""
    facts = ", ".join(
        f"{label.lower()} {blend[field]:g} {'kcal' if unit == 'kcal' else unit} per 100 g"
        for field, label, unit, _ in nutrition.NUTRIENT_ROWS
    )
    prompt = (
        f"Blend: {recipe_text(recipe_rows)}.\n"
        f"Computed by the app: {facts}; ingredient cost Rs {cost:,.2f} per kg.\n\n"
        "In at most 70 words: what stands out about this blend nutritionally, what it is best "
        "suited to (for example a snack base, a flatbread mix), and the one change most likely to "
        "improve it. Use the figures above only as given; do not recalculate or add new numbers."
    )
    return _generate(prompt, temperature=0.5, max_tokens=400).strip()


def explain_clean_label(items: list[dict]) -> str:
    """Why each flagged watchlist item is used in food, in the model's own words.

    Detection stays deterministic in `cleanlabel.py`; the model only explains what a flagged
    term is normally doing in a recipe.
    """
    names = ", ".join(
        f"{item['ingredient']['name']} ({item['why']})" for item in items
    )
    prompt = (
        f"These recipe items were flagged by a fixed additive watchlist: {names}.\n\n"
        "In at most 70 words, explain what role each normally plays in a snack formulation and "
        "what a home-kitchen style alternative would be. Do not judge whether the product is "
        "clean-label; the watchlist already decided that."
    )
    return _generate(prompt, temperature=0.5, max_tokens=400).strip()
