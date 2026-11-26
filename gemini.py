"""The only place SmartCrop.AI talks to cloud AI models (FreeLLMAPI router + Gemini fallback).

Ground rules, kept here so they cannot drift into a page:

* The model **never does arithmetic**. It reads the crop catalog and the recipe, proposes
  ingredient shares or explains a trade-off; `nutrition.py` computes every figure and
  `formulations.validate_items` is the gate every proposal must pass (real ids, shares total
  100 %, each crop under its practical cap).
* Keys live in `.env` only (`FREELM_API_KEY` / `GEMINI_API_KEY`). Nothing here prints them or
  hands them to the browser.
* When the FreeLLMAPI router is reachable, requests follow an ordered cascade of verified
  models with automatic failover on rate-limits, upstream errors, or invalid JSON; direct
  Google Gemini remains an automatic fallback, and `GeminiError` lets `whatif.py` take over
  cleanly if all cloud routes are down.

Plain `urllib` only — no SDK, no extra wheel to install on Python 3.14.
"""

from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

import ingredients
import nutrition
import skill_loader

APP_DIR = Path(__file__).resolve().parent
ENV_FILE = APP_DIR / ".env"
API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"
DEFAULT_ROUTER_BASE = "http://127.0.0.1:31415/v1"

# Verified FreeLLMAPI cascade ordered by SmartCrop benchmark reliability, accuracy, and speed.
ROUTER_MODELS = (
    "llama-3.3-70b-fp8-fast",
    "poolside-laguna-xs-2.1",
    "gpt-oss-20b",
    "auto",
)
ROUTER_CHOICES = (
    ("Smart Router (Auto)", ""),
    ("llama-3.3-70b-fp8-fast · 70B Fast", "llama-3.3-70b-fp8-fast"),
    ("poolside-laguna-xs-2.1 · Reasoning", "poolside-laguna-xs-2.1"),
    ("gpt-oss-20b · Balanced", "gpt-oss-20b"),
    ("auto · Dynamic route", "auto"),
    ("gpt-oss-120b · 120B", "gpt-oss-120b"),
)
ROUTER_KNOWN_IDS = {choice[1] for choice in ROUTER_CHOICES if choice[1]} | {"auto:smart"}

# Direct Google Gemini fallback list if the local FreeLLMAPI router is offline or unreachable.
FALLBACK_MODELS = (
    "gemini-flash-latest",
    "gemini-flash-lite-latest",
    "gemini-3.1-flash-lite",
    "gemini-3.1-flash-lite-preview",
    "gemini-pro-latest",
    "gemini-3-flash-preview",
)
TIMEOUT_SECONDS = 35
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
    """Read `.env` once per process: router settings, Gemini key, and model preferences."""
    key = (os.environ.get("GEMINI_API_KEY") or "").strip()
    preferred = (os.environ.get("GEMINI_MODEL") or "").strip()
    router_key = (os.environ.get("FREELM_API_KEY") or "").strip()
    router_base = (os.environ.get("FREELM_BASE_URL") or "").strip()
    router_preferred = (os.environ.get("FREELM_MODEL") or "").strip()

    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            name, _, value = line.partition("=")
            name = name.strip()
            value = value.strip().strip('"').strip("'")
            if name == "GEMINI_API_KEY" and not key:
                key = value
            elif name == "GEMINI_MODEL" and not preferred:
                preferred = value
            elif name == "FREELM_API_KEY" and not router_key:
                router_key = value
            elif name == "FREELM_BASE_URL" and not router_base:
                router_base = value
            elif name == "FREELM_MODEL" and not router_preferred:
                router_preferred = value

    router_base = (router_base or DEFAULT_ROUTER_BASE).rstrip("/")

    router_models: list[str] = []
    router_pref_seed = router_preferred or (
        preferred if (preferred in ROUTER_KNOWN_IDS or "/" in preferred) else ""
    )
    for candidate in (router_pref_seed, *ROUTER_MODELS):
        if candidate and candidate not in router_models:
            router_models.append(candidate)

    gemini_models: list[str] = []
    gemini_pref_seed = preferred if preferred.startswith("gemini-") else ""
    for candidate in (gemini_pref_seed, *FALLBACK_MODELS):
        if candidate and candidate not in gemini_models:
            gemini_models.append(candidate)

    return {
        "key": key,
        "router_key": router_key,
        "router_base": router_base,
        "models": gemini_models,
        "router_models": router_models,
        "preferred": preferred,
    }


def config() -> dict[str, object]:
    env_mtime = ENV_FILE.stat().st_mtime_ns if ENV_FILE.exists() else 0
    if not _config or _config.get("_env_mtime") != env_mtime:
        fresh = _load_config()
        fresh["_env_mtime"] = env_mtime
        _config.clear()
        _config.update(fresh)
    return _config


def reload_config() -> None:
    """Pick up `.env` updates while the app is running."""
    _config.clear()
    config()


def available() -> bool:
    cfg = config()
    return bool(cfg["router_key"] or cfg["key"])


def model_choices() -> tuple[tuple[str, str], ...]:
    """UI model choices for the current runtime configuration."""
    cfg = config()
    if cfg["router_key"]:
        return ROUTER_CHOICES
    if cfg["key"]:
        return (("Google Gemini (Auto)", ""), *((m, m) for m in cfg["models"]))
    return (("Offline rules", ""),)


def _short_model_name(raw: str, route: str = "") -> str:
    candidate = (raw or route or "").strip()
    if not candidate:
        return ""
    lowered = candidate.lower()
    if "laguna-xs-2.1" in lowered:
        return "poolside-laguna-xs-2.1"
    if "llama-3.3-70b" in lowered and "fp8-fast" in lowered:
        return "llama-3.3-70b-fp8-fast"
    if "/" in candidate:
        candidate = candidate.rsplit("/", 1)[-1]
    return candidate


def model_name() -> str:
    """The model that answered last, or the first preference when nothing has run yet."""
    cfg = config()
    if _config.get("last_model"):
        return str(_config["last_model"])
    if cfg["router_key"]:
        return str((cfg["router_models"] or ["auto"])[0])
    return str((cfg["models"] or ["gemini"])[0])


def status_label(selected: str | None = None) -> str:
    if not available():
        return "Local rules (no key)"
    cfg = config()
    selected_clean = (selected or "").strip()
    if selected_clean and _config.get("last_requested") != selected_clean:
        source = "Router" if cfg["router_key"] else "Gemini"
        return f"{source} · {selected_clean}"
    source = str(_config.get("last_source") or ("Router" if cfg["router_key"] else "Gemini"))
    current = str(_config.get("last_model") or selected_clean or model_name())
    return f"{source} · {current}"


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


def _router_http_message(code: int, body: str) -> tuple[str, bool]:
    snippet = ""
    try:
        err = json.loads(body).get("error")
        snippet = (err.get("message") if isinstance(err, dict) else str(err or "")) or ""
    except (ValueError, AttributeError):
        snippet = body[:160]
    if code == 401 or (
        code == 403 and any(w in snippet.upper() for w in ("KEY", "AUTH", "UNAUTHORIZED", "INVALID"))
    ):
        return ("The FreeLLMAPI key was rejected. Check FREELM_API_KEY in the .env file.", False)
    if code == 400:
        return (f"Router rejected parameters: {snippet}"[:220], True)
    if code == 404:
        return (f"Model unavailable on FreeLLMAPI router. {snippet}"[:220], True)
    if code == 429:
        return ("Router upstream model rate-limit hit; failing over.", True)
    if code in (500, 502, 503, 504):
        return (f"Router upstream model returned HTTP {code}; failing over.", True)
    return (f"Router returned HTTP {code}. {snippet}"[:220], True)


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


def _post_router(
    model: str,
    messages: list[dict[str, str]],
    *,
    temperature: float,
    max_tokens: int,
) -> tuple[str, str]:
    cfg = config()
    url = f"{cfg['router_base']}/chat/completions"
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {cfg['router_key']}",
            "User-Agent": "SmartCropAI/1.0",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            route_hdr = response.headers.get("x-routed-via") or response.headers.get("x-provider") or ""
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        message, retryable = _router_http_message(exc.code, exc.read().decode("utf-8", "replace"))
        raise GeminiError(message, retryable) from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        reason = getattr(exc, "reason", exc)
        err = GeminiError(f"Could not reach FreeLLMAPI router ({reason}).", True)
        err._router_unreachable = True  # type: ignore[attr-defined]
        raise err from exc

    choices = data.get("choices") or []
    if not choices:
        raise GeminiError("Router returned an empty choices list.", True)
    msg = choices[0].get("message") or {}
    text = re.sub(r"<think>.*?</think>", "", str(msg.get("content") or ""), flags=re.DOTALL).strip()
    if not text:
        finish = choices[0].get("finish_reason") or "no text"
        raise GeminiError(f"Router returned an empty answer ({finish}).", True)
    used_model = _short_model_name(str(data.get("model") or model), route_hdr) or model
    return text, used_model


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


def _router_system(system: str, schema: dict | None) -> str:
    if schema is RECIPE_SCHEMA:
        return (
            system
            + "\n\nRespond with ONLY a valid JSON object (no markdown fences, no extra text outside JSON) "
            "using these exact keys:\n"
            '- "reasoning": string — analyze user goal, product format, protein/cost/region/clean-label trade-offs across DB crops.\n'
            '- "selected_notes": string — summarize which ING-xxx ingredients you selected, adjusted, or excluded.\n'
            '- "reply": string — plain conversational sentences (<= 95 words, no markdown/bullets/emojis/ING-xxx codes), noting once it is a starting point needing lab validation.\n'
            '- "recipe": array of {"ingredient_id": "ING-xxx", "share_pct": number} totaling 100 (or [] if purely answering a question).'
        )
    if schema is DRAFT_SCHEMA:
        return (
            system
            + "\n\nRespond with ONLY a valid JSON object (no markdown fences, no extra text outside JSON) "
            "using these exact keys:\n"
            '- "name": string — 2 to 4 word product name.\n'
            '- "rationale": string — at most 60 plain words.\n'
            '- "recipe": array of {"ingredient_id": "ING-xxx", "share_pct": number} totaling 100.'
        )
    return system


def _ordered_candidates(preferred: str | None, pool: list[str] | tuple[str, ...]) -> list[str]:
    ordered: list[str] = []
    if preferred:
        ordered.append(preferred)
    for model in pool:
        if model not in ordered:
            ordered.append(model)
    return ordered


def _generate_via_router(
    prompt: str,
    *,
    system: str,
    schema: dict | None,
    temperature: float,
    max_tokens: int,
    model: str | None,
    expect_json: bool,
) -> tuple[str, dict | None]:
    cfg = config()
    selected = (model or "").strip()
    preferred = selected if (selected and (not selected.startswith("gemini-") or "/" in selected)) else None
    candidates = _ordered_candidates(preferred, cfg["router_models"])
    messages = [
        {"role": "system", "content": _router_system(system, schema)},
        {"role": "user", "content": prompt},
    ]
    effective_tokens = max(max_tokens, 1800 if schema is not None else 600)
    last_error: GeminiError | None = None

    for candidate in candidates:
        try:
            text, used_model = _post_router(
                candidate,
                messages,
                temperature=temperature,
                max_tokens=effective_tokens,
            )
            parsed = _json_of(text) if expect_json else None
        except GeminiError as exc:
            last_error = exc
            if getattr(exc, "_router_unreachable", False):
                break
            if not exc.retryable:
                raise
            continue
        _config["last_source"] = "Router"
        _config["last_model"] = used_model
        _config["last_requested"] = selected
        return text, parsed

    raise last_error or GeminiError("FreeLLMAPI router did not answer.", True)


def _generate_via_gemini(
    prompt: str,
    *,
    system: str,
    schema: dict | None,
    temperature: float,
    max_tokens: int,
    model: str | None,
    expect_json: bool,
) -> tuple[str, dict | None]:
    cfg = config()
    selected = (model or "").strip()
    preferred = selected if selected.startswith("gemini-") else None
    candidates = _ordered_candidates(preferred, cfg["models"])

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
    dead_models: set[str] = set()

    for attempt in range(2):
        if attempt > 0:
            time.sleep(1.5)
        for candidate in candidates:
            if candidate in dead_models:
                continue
            payload = json.loads(json.dumps(base_payload))
            if "lite" not in candidate.lower():
                payload["generationConfig"]["thinkingConfig"] = {"thinkingBudget": 1024}
                payload["generationConfig"]["maxOutputTokens"] = max(max_tokens, 2600)
            try:
                data = _post(candidate, payload)
            except GeminiError as exc:
                if "quota" in str(exc).lower() or "no longer available" in str(exc).lower():
                    dead_models.add(candidate)
                if exc.retryable:
                    last_error = exc
                    continue
                if "key" in str(exc).lower() and "rejected" in str(exc).lower():
                    raise
                if "thinkingConfig" not in payload["generationConfig"]:
                    last_error = exc
                    continue
                plain = json.loads(json.dumps(base_payload))
                plain["generationConfig"]["maxOutputTokens"] = max(max_tokens, 2000)
                try:
                    data = _post(candidate, plain)
                except GeminiError as retry_error:
                    last_error = retry_error
                    continue

            finish = ((data.get("candidates") or [{}])[0]).get("finishReason") or ""
            if finish == "MAX_TOKENS":
                last_error = GeminiError("Gemini ran out of room mid-answer.", True)
                continue
            text = _text_of(data)
            try:
                parsed = _json_of(text) if expect_json else None
            except GeminiError as exc:
                last_error = exc
                continue
            _config["last_source"] = "Gemini"
            _config["last_model"] = candidate
            _config["last_requested"] = selected
            return text, parsed

    raise last_error or GeminiError("Gemini did not answer.")


def _generate_core(
    prompt: str,
    *,
    system: str = SYSTEM_RULES,
    schema: dict | None = None,
    temperature: float = 0.4,
    max_tokens: int = 900,
    model: str | None = None,
    expect_json: bool = False,
) -> tuple[str, dict | None]:
    """Route through FreeLLMAPI cascade first, then direct Google Gemini if available."""
    if not available():
        raise GeminiError("No FreeLLMAPI or Gemini key is configured.")

    cfg = config()
    last_error: GeminiError | None = None

    if cfg["router_key"]:
        try:
            return _generate_via_router(
                prompt,
                system=system,
                schema=schema,
                temperature=temperature,
                max_tokens=max_tokens,
                model=model,
                expect_json=expect_json,
            )
        except GeminiError as exc:
            last_error = exc
            if not cfg["key"]:
                raise

    if cfg["key"]:
        try:
            return _generate_via_gemini(
                prompt,
                system=system,
                schema=schema,
                temperature=temperature,
                max_tokens=max_tokens,
                model=model,
                expect_json=expect_json,
            )
        except GeminiError as exc:
            raise exc if last_error is None else GeminiError(f"{last_error} Direct Gemini also failed: {exc}", exc.retryable) from exc

    raise last_error or GeminiError("No AI model answered.")


def _generate(
    prompt: str,
    *,
    system: str = SYSTEM_RULES,
    schema: dict | None = None,
    temperature: float = 0.4,
    max_tokens: int = 900,
    model: str | None = None,
) -> str:
    text, _ = _generate_core(
        prompt,
        system=system,
        schema=schema,
        temperature=temperature,
        max_tokens=max_tokens,
        model=model,
        expect_json=False,
    )
    return text


def _generate_json(
    prompt: str,
    *,
    system: str = SYSTEM_RULES,
    schema: dict | None = None,
    temperature: float = 0.4,
    max_tokens: int = 1600,
    model: str | None = None,
) -> dict:
    _, parsed = _generate_core(
        prompt,
        system=system,
        schema=schema,
        temperature=temperature,
        max_tokens=max_tokens,
        model=model,
        expect_json=True,
    )
    assert parsed is not None
    return parsed


def _json_of(text: str) -> dict:
    cleaned = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("```")[1] if "```" in cleaned[3:] else cleaned[3:]
        cleaned = cleaned.removeprefix("json").strip()
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start == -1 or end == -1:
        raise GeminiError("The model's answer was not readable.", True)
    try:
        payload = json.loads(cleaned[start : end + 1])
    except ValueError as exc:
        raise GeminiError("The model's answer was not readable.", True) from exc
    if not isinstance(payload, dict):
        raise GeminiError("The model's answer was not readable.", True)
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
    model: str | None = None,
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
            "0. First run the skill's turn check: NEW GOAL, REFINE or QUESTION. For a NEW GOAL rebuild from the "
            "whole database and treat the current recipe only as a comparison.\n"
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
    payload = _generate_json(
        prompt,
        schema=RECIPE_SCHEMA,
        max_tokens=1600,
        model=model,
        system=skill_loader.system_prompt(
            instruction,
            f"{project_name} {project_description}",
            recent=[m["text"] for m in reversed(history or []) if m["role"] == "user"][:3],
            fallback=SYSTEM_RULES,
        ),
    )
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


def draft(brief: str, *, project_name: str = "", cook: str = "", model: str | None = None) -> dict:
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
    payload = _generate_json(
        prompt,
        schema=DRAFT_SCHEMA,
        temperature=0.5,
        model=model,
        system=skill_loader.system_prompt(brief, f"{project_name} {cook}", fallback=SYSTEM_RULES),
    )

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


def explain_blend(
    recipe_rows: list[dict],
    blend: dict[str, float],
    cost: float,
    *,
    model: str | None = None,
) -> str:
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
    return _generate(prompt, temperature=0.5, max_tokens=400, model=model).strip()


def explain_clean_label(items: list[dict], *, model: str | None = None) -> str:
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
    return _generate(prompt, temperature=0.5, max_tokens=400, model=model).strip()
