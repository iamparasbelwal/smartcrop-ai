"""Loads the SmartCrop formulation skill (the `ai_skill/` folder) and builds the system prompt.

Every model in the app (the FreeLLMAPI router cascade and the direct Gemini fallbacks) gets the
same prompt on purpose: the app fails over between models in the middle of a request, so the
rules must not change when the model does.

The prompt is the always-on `SKILL.md` plus only the product-format section(s) that match the
user's message (a small stand-in for "load extra instructions when needed"). If the skill files
are missing or unreadable, the caller's fallback text is used, so the chat never breaks.
"""

from __future__ import annotations

import re
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent / "ai_skill"
MAX_PLAYBOOKS = 2

_cache: dict[str, str] = {}


def _read(name: str) -> str:
    if name not in _cache:
        _cache[name] = (SKILL_DIR / name).read_text(encoding="utf-8")
    return _cache[name]


def reload() -> None:
    """Pick up edits to the skill files while the app is running."""
    _cache.clear()


def _strip_frontmatter(text: str) -> str:
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) == 3:
            return parts[2].strip()
    return text.strip()


def _playbooks() -> list[dict]:
    """Parse product_formats.md into [{title, keywords, body}] sections."""
    sections = []
    for block in re.split(r"^## ", _read("product_formats.md"), flags=re.MULTILINE)[1:]:
        title, _, rest = block.partition("\n")
        match = re.search(r"<!--\s*keywords:(.*?)-->", rest, flags=re.DOTALL)
        keywords = [k.strip().lower() for k in (match.group(1) if match else "").split(",") if k.strip()]
        body = re.sub(r"<!--.*?-->\s*", "", rest, flags=re.DOTALL).strip()
        sections.append({"title": title.strip(), "keywords": keywords, "body": body})
    return sections


def _hits(text: str, keywords: list[str]) -> int:
    text = text.lower()
    return sum(
        1 for key in keywords if re.search(rf"\b{re.escape(key)}(?:s|es)?\b", text)
    )


def pick_playbooks(instruction: str, project_text: str = "", recent: list[str] | None = None) -> list[dict]:
    """The playbook sections for this message.

    The newest message decides: a request for a different product must not drag in the old
    product's playbook just because the project name still mentions it. When the message itself
    names no product format (for example "make it cheaper"), the user's recent messages are
    tried newest first, and the project text last.
    """
    sections = _playbooks()
    specific = [s for s in sections if s["keywords"]]
    for text in (instruction, *(recent or []), project_text):
        scored = [(_hits(text, s["keywords"]), i, s) for i, s in enumerate(specific)]
        scored = [item for item in scored if item[0] > 0]
        if scored:
            scored.sort(key=lambda item: (-item[0], item[1]))
            return [item[2] for item in scored[:MAX_PLAYBOOKS]]
    return [s for s in sections if not s["keywords"]]


def system_prompt(
    instruction: str = "",
    project_text: str = "",
    *,
    recent: list[str] | None = None,
    fallback: str = "",
) -> str:
    """Core skill + matching playbook(s). Returns `fallback` if the skill cannot be loaded."""
    try:
        core = _strip_frontmatter(_read("SKILL.md"))
        playbooks = pick_playbooks(instruction, project_text, recent)
    except (OSError, ValueError):
        return fallback
    if not core:
        return fallback
    parts = [core]
    if playbooks:
        parts.append(
            "## Product-format playbook for this message\n\n"
            + "\n\n".join(f"### {s['title']}\n{s['body']}" for s in playbooks)
        )
    return "\n\n".join(parts)
