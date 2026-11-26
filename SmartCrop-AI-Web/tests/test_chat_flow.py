"""6-turn sequential chat window & persistent chat history test on P-001."""

from __future__ import annotations

import http.cookiejar
import json
import time
import urllib.request

BASE = "http://127.0.0.1:8000"


def make_client() -> tuple[urllib.request.OpenerDirector, object, object]:
    jar = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))

    def post(path: str, body: dict) -> dict:
        req = urllib.request.Request(
            BASE + path,
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        return json.loads(op.open(req, timeout=70).read().decode("utf-8"))

    def get(path: str) -> dict:
        return json.loads(op.open(BASE + path, timeout=30).read().decode("utf-8"))

    return op, post, get


def main() -> None:
    _, post, get = make_client()
    post("/api/auth/login", {"email": "paras@smartcrop.ai", "password": "Admin@123"})
    post("/api/projects/P-001/chats/clear", {})
    post("/api/projects/P-001/region", {"target_region": "Maharashtra", "items": []})

    prompts = [
        "Create a high-protein, clean-label millet biscuit for Maharashtra schools under Rs 80/kg with low sugar and zero synthetic additives.",
        "Target Rajasthan instead and shift the main base grain toward pearl millet (bajra) to lower landed cost.",
        "Increase protein density above 18g per 100g using clean-label regional pulses or defatted groundnut flour.",
        "Reduce jaggery share for a less sweet, kids-balanced taste profile.",
        "Add a small amount of Sesame seeds for crisp biscuit texture and fibre while staying 100% clean-label.",
        "Fine-tune the shares to bring ingredient cost per kg down without dropping protein below 17g per 100g.",
    ]

    items: list = []
    history: list[dict] = []
    for idx, prompt in enumerate(prompts, 1):
        target_reg = "Maharashtra" if idx == 1 else "Rajasthan"
        if idx == 2:
            post("/api/projects/P-001/region", {"target_region": "Rajasthan", "items": items})
        t0 = time.perf_counter()
        res = post(
            "/api/studio/chat",
            {
                "project_id": "P-001",
                "items": items,
                "instruction": prompt,
                "mode": "formulation",
                "constraints": ["Clean Label", "Local Crops"],
                "target_region": target_reg,
                "history": history,
                "model": "",
            },
        )
        dt = time.perf_counter() - t0
        comp = res["computed"]
        items = comp["items"] or items
        blend = comp.get("blend") or {}
        reg = comp.get("regional") or {}
        history.append({"role": "user", "text": prompt})
        history.append({"role": "assistant", "text": res["reply"]})

        summary_line = (
            f"TURN {idx} ({dt:.2f}s) | engine={res['engine']} | changed={res['items_changed']} | "
            f"P={blend.get('protein_g')}g | E={blend.get('energy_kcal')}kcal | "
            f"mandi=Rs{comp.get('cost_per_kg')}/kg | landed=Rs{reg.get('landed_cost_per_kg')}/kg "
            f"({reg.get('local_share_pct')}% {reg.get('target_region')})"
        )
        print(summary_line)
        print(f"  PROMPT: {prompt}")
        print(f"  REPLY : {res['reply'].splitlines()[0]}")
        for row in comp.get("rows") or []:
            print(f"    - {row['name']} ({row['region']}, {row.get('region_tier')}): {row['share_pct']}%")

    save_res = post(
        "/api/studio/save",
        {"project_id": "P-001", "items": items, "name": "Millet Biscuit (6-Turn Tested)"},
    )
    print("SAVE:", save_res["message"])

    # Verify reload from a clean fresh session
    _, post2, get2 = make_client()
    post2("/api/auth/login", {"email": "paras@smartcrop.ai", "password": "Admin@123"})
    ws = get2("/api/projects/P-001/workspace")
    msg_count = len(ws.get("messages") or [])
    print(f"RELOADED WORKSPACE MESSAGES: {msg_count} (expected 12)")
    assert msg_count == 12, f"Expected 12 saved messages, got {msg_count}"
    print("SUCCESS: All 6 sequential chat turns executed & persisted to disk!")


if __name__ == "__main__":
    main()
