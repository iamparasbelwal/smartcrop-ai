"""Per-project persistent Co-Pilot chat history stored in data/chats/<project_id>.json."""

from __future__ import annotations

import json
import re
from pathlib import Path

from storage import DATA_DIR, now

CHATS_DIR = DATA_DIR / "chats"
MAX_MESSAGES = 60


def _chat_file(project_id: str) -> Path | None:
    safe = re.sub(r"[^A-Za-z0-9_-]", "", str(project_id or "").strip())
    if not safe:
        return None
    return CHATS_DIR / f"{safe}.json"


def list_messages(project_id: str) -> list[dict]:
    path = _chat_file(project_id)
    if not path or not path.is_file():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (OSError, ValueError):
        return []


def append_turn(
    project_id: str,
    user_text: str,
    assistant_payload: dict,
    *,
    user_id: str = "",
) -> list[dict]:
    path = _chat_file(project_id)
    if not path:
        return []
    CHATS_DIR.mkdir(parents=True, exist_ok=True)
    msgs = list_messages(project_id)
    ts = now()
    msgs.append(
        {
            "id": f"u-{len(msgs) + 1}",
            "role": "user",
            "text": user_text,
            "at": ts,
            "user_id": user_id,
        }
    )
    engine_str = str(assistant_payload.get("engine") or "")
    req_model = str(assistant_payload.get("requested_model") or "")
    fb_reason = str(assistant_payload.get("fallback_reason") or "")
    display_engine = f"{engine_str} (fallback from {req_model})" if (fb_reason and req_model and engine_str != req_model) else engine_str
    msgs.append(
        {
            "id": f"a-{len(msgs) + 1}",
            "role": "assistant",
            "text": str(assistant_payload.get("reply") or ""),
            "engine": display_engine,
            "thought": str(assistant_payload.get("thought") or ""),
            "thought_summary": str(assistant_payload.get("thought_summary") or ""),
            "at": ts,
        }
    )
    trimmed = msgs[-MAX_MESSAGES:]
    path.write_text(json.dumps(trimmed, ensure_ascii=False, indent=2), encoding="utf-8")
    return trimmed


def clear_messages(project_id: str) -> None:
    path = _chat_file(project_id)
    if path and path.is_file():
        path.unlink()
