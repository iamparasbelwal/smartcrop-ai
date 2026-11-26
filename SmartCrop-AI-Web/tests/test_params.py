"""Multi-parameter end-to-end verification suite for SmartCrop-AI-Web."""

from __future__ import annotations

import base64
import http.cookiejar
import json
import shutil
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

BASE_URL = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"


class Client:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.jar))

    def req(self, method: str, path: str, body: dict | None = None, timeout: int = 75) -> tuple[int, bytes, dict]:
        raw = json.dumps(body).encode("utf-8") if body is not None else None
        headers = {"Content-Type": "application/json"} if body is not None else {}
        request = urllib.request.Request(self.base_url + path, data=raw, method=method, headers=headers)
        try:
            with self.opener.open(request, timeout=timeout) as resp:
                return resp.status, resp.read(), dict(resp.headers)
        except urllib.error.HTTPError as exc:
            return exc.code, exc.read(), dict(exc.headers)

    def get_json(self, path: str) -> tuple[int, dict]:
        status, raw, _ = self.req("GET", path)
        return status, json.loads(raw.decode("utf-8"))

    def post_json(self, path: str, body: dict) -> tuple[int, dict]:
        status, raw, _ = self.req("POST", path, body)
        return status, json.loads(raw.decode("utf-8"))


def run_all() -> None:
    print(f"Testing SmartCrop-AI-Web at {BASE_URL}")
    anon = Client(BASE_URL)
    admin = Client(BASE_URL)
    worker = Client(BASE_URL)

    # 1. Static Assets & Path Guard
    static_paths = [
        "/",
        "/styles/tokens.css",
        "/styles/main.css",
        "/styles/app-extensions.css",
        "/src/icons.js",
        "/src/api.js",
        "/src/app.js",
        "/src/views/dashboard.js",
        "/src/views/studio.js",
        "/src/views/ingredients.js",
        "/src/views/formulations.js",
        "/src/views/admin.js",
        "/src/views/settings.js",
        "/assets/loading_biscuit_flask.gif",
    ]
    for p in static_paths:
        st_code, raw, _ = anon.req("GET", p)
        assert st_code == 200 and len(raw) > 50, f"Static {p} failed ({st_code})"
    st_trav, _, _ = anon.req("GET", "/../.env")
    assert st_trav in (403, 404), f"Traversal returned {st_trav}"
    print("[PASS] Suite 1: All 15 static UI assets & security path guard passed")

    # 2. Auth & Role Guards
    st_code, _ = anon.get_json("/api/projects")
    assert st_code == 401, f"Expected 401 unauthenticated, got {st_code}"
    st_bad, _ = anon.post_json("/api/auth/login", {"email": "paras@smartcrop.ai", "password": "wrong"})
    assert st_bad == 401
    st_adm, d_adm = admin.post_json("/api/auth/login", {"email": "paras@smartcrop.ai", "password": "Admin@123"})
    assert st_adm == 200 and d_adm["user"]["role"] == "lab_admin"
    st_wrk, d_wrk = worker.post_json("/api/auth/login", {"email": "shivam@smartcrop.ai", "password": "Worker@123"})
    assert st_wrk == 200 and d_wrk["user"]["role"] == "lab_worker"
    st_forbid, _ = worker.get_json("/api/admin/overview")
    assert st_forbid == 403, f"Worker reached admin overview ({st_forbid})"
    print("[PASS] Suite 2: Auth credentials, cookies & RBAC role isolation passed")

    # 3. Project Creation & Access Grant/Revoke Parameters
    st_p, d_p = admin.post_json(
        "/api/projects",
        {"name": "Param Test Millet Biscuit", "description": "Uttarakhand high protein snack"},
    )
    assert st_p == 201, d_p
    pid = d_p["project_id"]
    _, w_before = worker.get_json("/api/projects")
    assert not any(p["project_id"] == pid for p in w_before["projects"]), "Worker saw private project pre-grant"
    st_gr, _ = admin.post_json("/api/admin/access", {"project_id": pid, "user_id": "U-002", "grant": True})
    assert st_gr == 200
    _, w_after = worker.get_json("/api/projects")
    assert any(p["project_id"] == pid for p in w_after["projects"]), "Worker still missed project post-grant"
    admin.post_json("/api/admin/access", {"project_id": pid, "user_id": "U-002", "grant": False})
    _, w_revoked = worker.get_json("/api/projects")
    assert not any(p["project_id"] == pid for p in w_revoked["projects"])
    print("[PASS] Suite 3: Project isolation + Grant/Revoke access parameters passed")

    # 4. Health & Router Parameters
    st_h, d_h = admin.get_json("/api/health")
    assert st_h == 200 and d_h["skill_loaded"], d_h
    print(f"[PASS] Suite 4: Health check OK (router_reachable={d_h['router_reachable']}, skill_loaded={d_h['skill_loaded']})")

    # 5. Multi-Mode & Multi-Model Formulation Parameters
    t0 = time.perf_counter()
    st_c1, d_c1 = admin.post_json(
        "/api/studio/chat",
        {
            "project_id": pid,
            "items": [],
            "instruction": "High-protein clean-label millet biscuit for Uttarakhand school kids, low cost",
            "mode": "formulation",
            "constraints": ["Clean Label", "Local Crops"],
            "model": "",
            "history": [],
        },
    )
    dt1 = time.perf_counter() - t0
    assert st_c1 == 200 and d_c1["items_changed"] and d_c1["engine"] != "local", d_c1
    items1 = d_c1["computed"]["items"]
    ids1 = {k for k, _ in items1}
    assert "ING-005" not in ids1, f"Clean-label check violated with ING-005: {items1}"
    assert abs(d_c1["computed"]["total_pct"] - 100.0) <= 0.2
    print(
        f"[PASS] Suite 5a (Formulation Mode, Auto Router, {dt1:.2f}s): engine={d_c1['engine']}, "
        f"crops={len(items1)}, protein={d_c1['computed']['blend']['protein_g']}g, cost=₹{d_c1['computed']['cost_per_kg']}/kg"
    )

    t0 = time.perf_counter()
    st_c2, d_c2 = admin.post_json(
        "/api/studio/chat",
        {
            "project_id": pid,
            "items": items1,
            "instruction": "Actually pivot to a savory gluten-free plant-based nugget using pulses",
            "mode": "crop-research",
            "constraints": ["Gluten-Free", "Clean Label"],
            "model": "llama-3.3-70b-fp8-fast",
            "history": [
                {"role": "user", "text": "High-protein clean-label millet biscuit"},
                {"role": "assistant", "text": d_c1["reply"]},
            ],
        },
    )
    dt2 = time.perf_counter() - t0
    assert st_c2 == 200 and d_c2["items_changed"], d_c2
    items2 = d_c2["computed"]["items"]
    ids2 = {k for k, _ in items2}
    assert "ING-011" not in ids2 and "ING-012" not in ids2, f"Gluten-free savory nugget had wheat/jaggery: {items2}"
    print(f"[PASS] Suite 5b (Crop Research Pivot Mode, llama-3.3-70b-fp8-fast, {dt2:.2f}s): nugget crops={len(items2)}")

    t0 = time.perf_counter()
    st_c3, d_c3 = admin.post_json(
        "/api/studio/chat",
        {
            "project_id": pid,
            "items": items2,
            "instruction": "Make it cheaper while maintaining high protein",
            "mode": "optimization",
            "constraints": ["Cost Target", "Max Protein"],
            "model": "poolside-laguna-xs-2.1",
            "history": [],
        },
    )
    dt3 = time.perf_counter() - t0
    assert st_c3 == 200 and abs(d_c3["computed"]["total_pct"] - 100.0) <= 0.2, d_c3
    print(f"[PASS] Suite 5c (Optimization Mode, poolside-laguna-xs-2.1, {dt3:.2f}s): engine={d_c3['engine']}, cost=₹{d_c3['computed']['cost_per_kg']}/kg")

    st_q, d_q = admin.post_json(
        "/api/studio/chat",
        {
            "project_id": pid,
            "items": items2,
            "instruction": "Why chickpea flour instead of defatted soy flour?",
            "mode": "nutrition",
            "constraints": ["Clean Label"],
            "model": "",
            "history": [],
        },
    )
    assert st_q == 200 and not d_q["items_changed"], f"Question modified recipe unexpectedly: {d_q}"
    print(f"[PASS] Suite 5d (Nutrition Question Mode): blend preserved, engine={d_q['engine']}")

    # 6. Deterministic Validation Caps, Swaps, Draft, Explain, Save, Compare & Spec Export
    st_badcap, _ = admin.post_json(
        "/api/studio/compute",
        {"items": [["ING-001", 60], ["ING-005", 30], ["ING-013", 10]], "validate": True},
    )
    assert st_badcap == 400, f"Infeasible cap total (87% < 100%) should return 400, got {st_badcap}"

    st_cap, d_cap = admin.post_json(
        "/api/studio/compute",
        {"items": [["ING-001", 58], ["ING-007", 30], ["ING-005", 20], ["ING-013", 10]], "validate": True},
    )
    cap_map = dict(d_cap["computed"]["items"])
    assert st_cap == 200 and cap_map.get("ING-013", 0) <= 2.0 and cap_map.get("ING-001", 0) <= 60.0
    assert d_cap["computed"]["review_count"] >= 1, "Expected ING-005 review finding"
    st_sw, d_sw = admin.post_json(
        "/api/studio/compute",
        {"items": [["ING-001", 60], ["ING-007", 38], ["ING-013", 2]], "validate": True},
    )
    assert st_sw == 200 and d_sw["computed"]["review_count"] == 0 and d_sw["computed"]["flagged_count"] == 0

    st_s1, _ = admin.post_json("/api/studio/save", {"project_id": pid, "items": items1, "name": "Biscuit Base"})
    st_s2, _ = admin.post_json("/api/studio/save", {"project_id": pid, "items": items2, "name": "Nugget Pivot"})
    assert st_s1 == 200 and st_s2 == 200
    st_ws, d_ws = admin.get_json(f"/api/projects/{pid}/workspace")
    assert st_ws == 200 and len(d_ws["versions"]) == 2 and len(d_ws["compare"]["rows"]) > 0
    st_ex, d_ex = admin.post_json("/api/studio/export", {"project_id": pid, "items": items2})
    assert st_ex == 200 and "SMARTCROP.AI" in d_ex["markdown"]

    st_dr, d_dr = admin.post_json(
        "/api/studio/draft",
        {"brief": "Clean-label roasted millet bar", "cook": "Baked snack", "project_name": "Millet Bar"},
    )
    assert st_dr == 200 and d_dr["computed"]["total_pct"] == 100.0
    st_eb, d_eb = admin.post_json("/api/studio/explain", {"kind": "blend", "items": items1})
    assert st_eb == 200 and len(d_eb["text"]) > 15
    print("[PASS] Suite 6: Cap validation, clean-label check/swap, versioning A vs B, spec export, AI draft & explain passed")

    # 7. Crop Creation, Verification + Attachment Upload & Worker Lifecycle
    st_ing, d_ing = admin.post_json(
        "/api/ingredients",
        {"name": "Test Barnyard Millet", "local_name": "Jhangora", "category": "Millet", "region": "Uttarakhand", "protein_g": 11.2, "cost_per_kg": 80, "max_practical_pct": 45},
    )
    assert st_ing == 201
    fake_pdf = base64.b64encode(b"Test Lab COA Report OK").decode("ascii")
    st_ver, d_ver = admin.post_json(
        "/api/ingredients/ING-001/verify",
        {
            "values": {"cost_per_kg": 46.5},
            "nutrition_confidence": "verified",
            "cost_confidence": "verified",
            "reference": "Lab Test COA",
            "report_name": "coa.txt",
            "report_b64": fake_pdf,
        },
    )
    assert st_ver == 200
    _, d_adm_ov = admin.get_json("/api/admin/overview")
    rep_ev = next((e for e in d_adm_ov["audit"] if e.get("lab_report")), None)
    assert rep_ev is not None
    st_dl, raw_dl, _ = admin.req("GET", f"/api/audit/{rep_ev['event_id']}/report")
    assert st_dl == 200 and raw_dl == b"Test Lab COA Report OK"

    st_wnew, _ = admin.post_json("/api/admin/users", {"name": "Test Tech", "email": "tech@lab.org", "password": "Password123"})
    assert st_wnew == 201
    _, ov2 = admin.get_json("/api/admin/overview")
    tech = next(u for u in ov2["users"] if u["email"] == "tech@lab.org")
    admin.post_json(f"/api/admin/users/{tech['user_id']}/toggle", {"active": False})
    st_deact, _ = Client(BASE_URL).post_json("/api/auth/login", {"email": "tech@lab.org", "password": "Password123"})
    assert st_deact == 401
    print("[PASS] Suite 7: Crop CRUD, verification + report download & worker lifecycle passed")

    # 8. Region-Specific Ingredient Targeting & Landed Cost Optimization
    st_pr_ka, d_pr_ka = admin.post_json(
        "/api/projects",
        {"name": "Karnataka Millet Biscuit", "description": "Low-cost regional clean-label snack", "target_region": "Karnataka"},
    )
    assert st_pr_ka == 201, d_pr_ka
    ka_pid = d_pr_ka["project_id"]
    st_ka_chat, d_ka_chat = admin.post_json(
        "/api/studio/chat",
        {
            "project_id": ka_pid,
            "items": [],
            "instruction": "Build a clean-label high-protein millet biscuit under ₹80/kg optimizing regional Karnataka sourcing.",
            "mode": "formulation",
            "constraints": ["Clean Label", "Local Crops"],
            "target_region": "Karnataka",
            "model": "",
            "history": [],
        },
    )
    assert st_ka_chat == 200 and d_ka_chat["items_changed"], d_ka_chat
    reg_ka = d_ka_chat["computed"]["regional"]
    assert reg_ka["target_region"] == "Karnataka" and reg_ka["is_targeted"], reg_ka
    assert reg_ka["local_share_pct"] >= 50.0, f"Expected strong regional sourcing for Karnataka, got {reg_ka}"

    st_reg_sw, d_reg_sw = admin.post_json(
        f"/api/projects/{ka_pid}/region",
        {"target_region": "Rajasthan", "items": d_ka_chat["computed"]["items"]},
    )
    assert st_reg_sw == 200 and d_reg_sw["target_region"] == "Rajasthan"
    assert d_reg_sw["computed"]["regional"]["target_region"] == "Rajasthan"
    print(
        f"[PASS] Suite 8: Regional cost targeting passed "
        f"(Karnataka local_share={reg_ka['local_share_pct']}%, landed=₹{reg_ka['landed_cost_per_kg']}/kg, saved=₹{reg_ka['savings_vs_distant']}/kg)"
    )

    print("\nALL 8 PARAMETRIC TEST SUITES PASSED SUCCESSFULLY")


if __name__ == "__main__":
    backup_dir = Path(tempfile.mkdtemp(prefix="smartcrop_web_bak_"))
    shutil.copytree(DATA_DIR, backup_dir / "data")
    try:
        run_all()
    finally:
        # Restore pristine seeded CSV/report snapshot after destructive parameter tests
        for item in DATA_DIR.iterdir():
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()
        for item in (backup_dir / "data").iterdir():
            if item.is_dir():
                shutil.copytree(item, DATA_DIR / item.name)
            else:
                shutil.copy2(item, DATA_DIR / item.name)
        shutil.rmtree(backup_dir, ignore_errors=True)
        print("Restored clean SmartCrop-AI-Web/data snapshot.")
