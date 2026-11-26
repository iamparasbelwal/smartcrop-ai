"""SmartCrop.AI Hybrid Web Server (Shivam botanical frontend + SmartCrop Python backend).

Run:
    python server.py --port 8000
"""

from __future__ import annotations

import argparse
import base64
import csv
import io
import json
import mimetypes
import secrets
import sys
import threading
import urllib.parse
import urllib.request
from http import cookies
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"
WEB_DIR = ROOT_DIR / "web"

sys.path.insert(0, str(BACKEND_DIR))

import access  # noqa: E402
import auth  # noqa: E402
import chats  # noqa: E402
import cleanlabel  # noqa: E402
import copilot  # noqa: E402
import formulations  # noqa: E402
import gemini  # noqa: E402
import ingredients  # noqa: E402
import nutrition  # noqa: E402
import projects  # noqa: E402
import regions  # noqa: E402
import skill_loader  # noqa: E402

DATA_LOCK = threading.RLock()
SESSIONS: dict[str, str] = {}
SESSION_COOKIE = "smartcrop_sid"


def _bootstrap_all() -> None:
    auth.bootstrap()
    projects.bootstrap()
    ingredients.bootstrap()
    cleanlabel.bootstrap()
    formulations.bootstrap()


def _serialize_ingredient(row: dict[str, str]) -> dict:
    p_path = ingredients.photo_path(row["ingredient_id"])
    photo_url = (
        f"/api/ingredients/{row['ingredient_id']}/photo?v={int(p_path.stat().st_mtime)}"
        if p_path
        else ""
    )
    return {
        "ingredient_id": row["ingredient_id"],
        "name": row["name"],
        "local_name": row.get("local_name", ""),
        "category": row.get("category", "Crop"),
        "region": row.get("region", ""),
        "energy_kcal": ingredients.number(row, "energy_kcal"),
        "protein_g": ingredients.number(row, "protein_g"),
        "fat_g": ingredients.number(row, "fat_g"),
        "carbs_g": ingredients.number(row, "carbs_g"),
        "fibre_g": ingredients.number(row, "fibre_g"),
        "moisture_g": ingredients.number(row, "moisture_g"),
        "cost_per_kg": ingredients.number(row, "cost_per_kg"),
        "cost_per_100g": round(ingredients.cost_per_100g(row), 2),
        "max_practical_pct": ingredients.number(row, "max_practical_pct"),
        "is_clean_label": row.get("is_clean_label", "yes"),
        "clean_label_note": row.get("clean_label_note", ""),
        "nutrition_confidence": row.get("nutrition_confidence", "estimated"),
        "cost_confidence": row.get("cost_confidence", "estimated"),
        "cost_date": row.get("cost_date", ""),
        "source_id": row.get("source_id", ""),
        "updated_at": row.get("updated_at", ""),
        "photo_url": photo_url,
    }


def _compute_payload(items: list[tuple[str, float]], target_region: str = "Pan-India") -> dict:
    reg_norm = regions.normalize_region(target_region)
    if not items:
        return {
            "items": [],
            "rows": [],
            "blend": {},
            "cost_per_kg": 0.0,
            "cost_per_serving": 0.0,
            "serving_grams": nutrition.SERVING_GRAMS,
            "baseline_cost": round(nutrition.cost_per_kg(formulations.reference_base()), 2),
            "delta_pct": 0.0,
            "confidence": {"verified": 0, "estimated": 0, "unknown": 0},
            "findings": [],
            "flagged_count": 0,
            "review_count": 0,
            "total_pct": 0.0,
            "regional": regions.evaluate_blend([], reg_norm),
        }

    resolved = formulations.resolve(items)
    blend = nutrition.blend_nutrition(resolved)
    cost = round(nutrition.cost_per_kg(resolved), 2)
    serving_cost = round(nutrition.cost_per_serving(resolved), 2)
    baseline = round(nutrition.cost_per_kg(formulations.reference_base()), 2)
    delta_pct = round(((cost - baseline) / baseline * 100) if baseline else 0.0, 1)
    raw_findings = cleanlabel.check(resolved)
    reg_eval = regions.evaluate_blend(resolved, reg_norm)

    findings = [
        {
            "ingredient_id": item["ingredient"]["ingredient_id"],
            "name": item["ingredient"]["name"],
            "status": item["status"],
            "why": item["why"],
            "replacement_note": item["replacement_note"],
            "option": (
                {
                    "ingredient_id": item["option"]["ingredient_id"],
                    "name": item["option"]["name"],
                    "cost_per_100g": round(ingredients.cost_per_100g(item["option"]), 2),
                }
                if item.get("option")
                else None
            ),
        }
        for item in raw_findings
    ]
    rows = []
    for r in resolved:
        landed, tier, freight = regions.effective_cost_per_kg(r["ingredient"], reg_norm)
        rows.append(
            _serialize_ingredient(r["ingredient"])
            | {
                "share_pct": round(float(r["share_pct"]), 1),
                "region_tier": tier,
                "freight_per_kg": freight,
                "landed_cost_per_kg": landed,
            }
        )
    return {
        "items": [[k, round(float(v), 1)] for k, v in items],
        "rows": rows,
        "blend": blend,
        "cost_per_kg": cost,
        "cost_per_serving": serving_cost,
        "serving_grams": nutrition.SERVING_GRAMS,
        "baseline_cost": baseline,
        "delta_pct": delta_pct,
        "confidence": nutrition.confidence_counts(resolved),
        "findings": findings,
        "flagged_count": sum(1 for f in findings if f["status"] == "flagged"),
        "review_count": sum(1 for f in findings if f["status"] == "review"),
        "total_pct": round(sum(float(v) for _, v in items), 1),
        "regional": reg_eval,
    }


def _parse_items(raw: object) -> list[tuple[str, float]]:
    if not isinstance(raw, list):
        return []
    pairs: list[tuple[str, float]] = []
    for entry in raw:
        if isinstance(entry, (list, tuple)) and len(entry) == 2:
            try:
                pairs.append((str(entry[0]).strip(), float(entry[1])))
            except (TypeError, ValueError):
                continue
        elif isinstance(entry, dict) and entry.get("ingredient_id"):
            try:
                pairs.append((str(entry["ingredient_id"]).strip(), float(entry.get("share_pct") or 0)))
            except (TypeError, ValueError):
                continue
    return pairs


def _project_summary_list(user: dict[str, str]) -> list[dict]:
    names = auth.user_names()
    out = []
    for proj in projects.list_visible_projects(user):
        latest, items = formulations.get_latest_project_formulation(proj["project_id"])
        metrics = None
        if items:
            resolved = formulations.resolve(items)
            blend = nutrition.blend_nutrition(resolved)
            metrics = {
                "protein_g": blend.get("protein_g", 0),
                "energy_kcal": blend.get("energy_kcal", 0),
                "cost_per_kg": round(nutrition.cost_per_kg(resolved), 2),
                "crop_count": len(resolved),
            }
        out.append(
            proj
            | {
                "creator_name": names.get(proj["created_by"], proj["created_by"]),
                "latest_version": int(latest["version"]) if latest else 0,
                "latest_formulation_id": latest["formulation_id"] if latest else "",
                "metrics": metrics,
            }
        )
    return out


class SmartCropHandler(BaseHTTPRequestHandler):
    server_version = "SmartCropAIWeb/2.0"

    def log_message(self, format: str, *args) -> None:
        pass

    def _send_json(self, status: int, payload: object, extra_headers: list[tuple[str, str]] | None = None) -> None:
        raw = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        for k, v in extra_headers or []:
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(raw)

    def _send_bytes(self, status: int, content_type: str, data: bytes, disposition: str = "") -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        if disposition:
            self.send_header("Content-Disposition", disposition)
        self.end_headers()
        self.wfile.write(data)

    def _read_json(self) -> dict:
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            length = 0
        if length <= 0:
            return {}
        raw = self.rfile.read(min(length, 15 * 1024 * 1024))
        try:
            data = json.loads(raw.decode("utf-8"))
            return data if isinstance(data, dict) else {}
        except ValueError:
            return {}

    def _session_token(self) -> str:
        header_tok = (self.headers.get("X-Session-Token") or "").strip()
        if header_tok:
            return header_tok
        raw_cookie = self.headers.get("Cookie") or ""
        if raw_cookie:
            jar = cookies.SimpleCookie()
            jar.load(raw_cookie)
            if SESSION_COOKIE in jar:
                return jar[SESSION_COOKIE].value
        return ""

    def _current_user(self) -> dict[str, str] | None:
        tok = self._session_token()
        if not tok:
            return None
        with DATA_LOCK:
            uid = SESSIONS.get(tok)
            if not uid:
                return None
            user = auth.get_user(uid)
            if user is None:
                SESSIONS.pop(tok, None)
                return None
            return user

    def _require_user(self) -> dict[str, str] | None:
        user = self._current_user()
        if user is None:
            self._send_json(401, {"error": "Authentication required."})
            return None
        return user

    def _require_admin(self) -> dict[str, str] | None:
        user = self._require_user()
        if user is None:
            return None
        if user.get("role") != "lab_admin":
            self._send_json(403, {"error": "Only lab administrators can perform this action."})
            return None
        return user

    def _serve_static(self, raw_path: str) -> None:
        rel = urllib.parse.unquote(raw_path.split("?", 1)[0]).lstrip("/") or "index.html"
        target = (WEB_DIR / rel).resolve()
        try:
            if not target.is_relative_to(WEB_DIR.resolve()):
                self._send_json(403, {"error": "Forbidden"})
                return
        except ValueError:
            self._send_json(403, {"error": "Forbidden"})
            return
        if target.is_dir():
            target = target / "index.html"
        if not target.is_file():
            self._send_json(404, {"error": "Not found"})
            return
        ctype, _ = mimetypes.guess_type(target.name)
        if target.suffix == ".js":
            ctype = "application/javascript; charset=utf-8"
        elif target.suffix == ".css":
            ctype = "text/css; charset=utf-8"
        elif target.suffix == ".html":
            ctype = "text/html; charset=utf-8"
        self._send_bytes(200, ctype or "application/octet-stream", target.read_bytes())

    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        qs = urllib.parse.parse_qs(parsed.query)

        if not path.startswith("/api/"):
            self._serve_static(path)
            return

        if path == "/api/bootstrap":
            with DATA_LOCK:
                user = self._current_user()
                all_ings = ingredients.list_ingredients()
                vcounts = ingredients.verified_counts()
                audit = auth.read_audit_log() if user else []
                vis_projects = _project_summary_list(user) if user else []
                total_formulations = sum(p["latest_version"] for p in vis_projects)
                self._send_json(
                    200,
                    {
                        "user": user,
                        "lab_id": auth.LAB_ID,
                        "lab_name": auth.LAB_NAME,
                        "ai": {
                            "available": gemini.available(),
                            "status": gemini.status_label(),
                            "model": gemini.model_name(),
                            "choices": [{"label": lbl, "value": val} for lbl, val in gemini.model_choices()],
                        },
                        "stats": {
                            "projects_count": len(vis_projects),
                            "formulations_count": total_formulations,
                            "ingredients_count": len(all_ings),
                            "nutrition_verified": vcounts["nutrition_verified"],
                            "cost_verified": vcounts["cost_verified"],
                            "audit_count": len(audit),
                        },
                        "projects": vis_projects,
                        "target_regions": list(regions.TARGET_REGIONS),
                        "recent_audit": audit[:6] if (user and user["role"] == "lab_admin") else [],
                        "user_names": auth.user_names() if user else {},
                    },
                )
            return

        if path == "/api/health":
            user = self._require_user()
            if not user:
                return
            cfg = gemini.config()
            router_reachable = False
            router_error = ""
            if cfg.get("router_key"):
                try:
                    req = urllib.request.Request(
                        f"{cfg['router_base']}/models",
                        headers={"Authorization": f"Bearer {cfg['router_key']}"},
                    )
                    with urllib.request.urlopen(req, timeout=4) as resp:
                        router_reachable = resp.status == 200
                except Exception as exc:
                    router_error = str(exc)
            skill_ok = bool(skill_loader.system_prompt("high protein millet biscuit", "Millet snack"))
            self._send_json(
                200,
                {
                    "ok": True,
                    "router_configured": bool(cfg.get("router_key")),
                    "router_base": cfg.get("router_base", ""),
                    "router_reachable": router_reachable,
                    "router_error": router_error,
                    "gemini_fallback_configured": bool(cfg.get("key")),
                    "router_models": list(cfg.get("router_models") or []),
                    "skill_loaded": skill_ok,
                    "status": gemini.status_label(),
                },
            )
            return

        if path == "/api/projects":
            user = self._require_user()
            if not user:
                return
            with DATA_LOCK:
                self._send_json(200, {"projects": _project_summary_list(user)})
            return

        if path.startswith("/api/projects/") and path.endswith("/workspace"):
            user = self._require_user()
            if not user:
                return
            pid = path.split("/")[3]
            with DATA_LOCK:
                proj = projects.get_project(pid)
                if not proj or not access.can_view(proj, user):
                    self._send_json(404, {"error": "Project not found or access denied."})
                    return
                versions = formulations.list_project_formulations(pid)
                req_ver = (qs.get("version") or [""])[0]
                if req_ver:
                    active_meta = next((v for v in versions if v["formulation_id"] == req_ver), None)
                    items = formulations.formulation_items(req_ver) if active_meta else []
                else:
                    active_meta, items = formulations.get_latest_project_formulation(pid)

                cmp_a_id = (qs.get("cmp_a") or [versions[min(1, len(versions) - 1)]["formulation_id"] if versions else ""])[0]
                cmp_b_id = (qs.get("cmp_b") or [versions[0]["formulation_id"] if versions else ""])[0]
                cmp_rows = []
                if cmp_a_id and cmp_b_id and cmp_a_id != cmp_b_id:
                    for row in formulations.compare_items(
                        formulations.formulation_items(cmp_a_id),
                        formulations.formulation_items(cmp_b_id),
                    ):
                        cmp_rows.append(
                            {
                                "ingredient_id": row["ingredient"]["ingredient_id"],
                                "name": row["ingredient"]["name"],
                                "share_a": row["share_a"],
                                "share_b": row["share_b"],
                                "delta": row["delta"],
                            }
                        )

                names = auth.user_names()
                self._send_json(
                    200,
                    {
                        "project": proj | {"creator_name": names.get(proj["created_by"], proj["created_by"])},
                        "latest_meta": active_meta,
                        "versions": [
                            v | {"creator_name": names.get(v["created_by"], v["created_by"]), "item_count": len(formulations.formulation_items(v["formulation_id"]))}
                            for v in versions
                        ],
                        "compare": {"cmp_a": cmp_a_id, "cmp_b": cmp_b_id, "rows": cmp_rows},
                        "computed": _compute_payload(items, proj.get("target_region") or "Pan-India"),
                        "messages": chats.list_messages(pid),
                    },
                )
            return

        if path.startswith("/api/ingredients/") and path.endswith("/photo"):
            user = self._require_user()
            if not user:
                return
            iid = path.split("/")[3]
            with DATA_LOCK:
                ppath = ingredients.photo_path(iid)
                if not ppath:
                    self._send_json(404, {"error": "No photo uploaded for this ingredient."})
                    return
                ctype, _ = mimetypes.guess_type(ppath.name)
                self._send_bytes(200, ctype or "image/jpeg", ppath.read_bytes())
            return

        if path == "/api/ingredients":
            user = self._require_user()
            if not user:
                return
            with DATA_LOCK:
                rows = [_serialize_ingredient(r) for r in ingredients.list_ingredients()]
                self._send_json(
                    200,
                    {
                        "ingredients": rows,
                        "counts": ingredients.verified_counts(),
                        "watchlist": cleanlabel.watchlist(),
                    },
                )
            return

        if path == "/api/admin/overview":
            user = self._require_admin()
            if not user:
                return
            with DATA_LOCK:
                users_list = auth.list_users(user["lab_id"])
                active_users = [u for u in users_list if u["active"] == "yes"]
                all_projects = projects.list_projects(user["lab_id"])
                access_matrix = []
                for proj in all_projects:
                    granted = {row["user_id"] for row in access.list_grants(proj["project_id"])}
                    access_matrix.append(
                        {
                            "project": proj,
                            "visible_count": sum(1 for u in active_users if access.can_view(proj, u)),
                            "members": [
                                {
                                    "user_id": u["user_id"],
                                    "name": u["name"],
                                    "email": u["email"],
                                    "role": u["role"],
                                    "always": u["role"] == "lab_admin" or u["user_id"] == proj["created_by"],
                                    "always_reason": "Creator" if u["user_id"] == proj["created_by"] else ("Lab admin" if u["role"] == "lab_admin" else ""),
                                    "has_access": u["user_id"] in granted or u["role"] == "lab_admin" or u["user_id"] == proj["created_by"],
                                }
                                for u in active_users
                            ],
                        }
                    )
                audit = auth.read_audit_log()
                self._send_json(
                    200,
                    {
                        "users": users_list,
                        "user_names": auth.user_names(),
                        "access_matrix": access_matrix,
                        "audit": audit[:250],
                        "total_audit": len(audit),
                        "verified_counts": ingredients.verified_counts(),
                    },
                )
            return

        if path.startswith("/api/audit/") and path.endswith("/report"):
            user = self._require_admin()
            if not user:
                return
            eid = path.split("/")[3]
            with DATA_LOCK:
                event = next((e for e in auth.read_audit_log() if e["event_id"] == eid), None)
                if not event or not event.get("lab_report"):
                    self._send_json(404, {"error": "No lab report attached."})
                    return
                rpath = auth.lab_report_path(event["lab_report"])
                if not rpath:
                    self._send_json(404, {"error": "Report file missing on disk."})
                    return
                ctype, _ = mimetypes.guess_type(rpath.name)
                self._send_bytes(
                    200,
                    ctype or "application/octet-stream",
                    rpath.read_bytes(),
                    disposition=f'attachment; filename="{rpath.name}"',
                )
            return

        if path == "/api/audit/csv":
            user = self._require_admin()
            if not user:
                return
            with DATA_LOCK:
                rows = auth.read_audit_log()
                buf = io.StringIO()
                writer = csv.DictWriter(buf, fieldnames=auth.AUDIT_FIELDS)
                writer.writeheader()
                writer.writerows(rows)
                self._send_bytes(
                    200,
                    "text/csv; charset=utf-8",
                    buf.getvalue().encode("utf-8"),
                    disposition='attachment; filename="smartcrop_audit_log.csv"',
                )
            return

        self._send_json(404, {"error": "Unknown API endpoint."})

    def do_POST(self) -> None:
        path = urllib.parse.urlparse(self.path).path
        body = self._read_json()

        if path == "/api/auth/login":
            with DATA_LOCK:
                ok, msg, user = auth.authenticate(str(body.get("email") or ""), str(body.get("password") or ""))
                if not ok or user is None:
                    self._send_json(401, {"error": msg})
                    return
                tok = secrets.token_urlsafe(24)
                SESSIONS[tok] = user["user_id"]
                self._send_json(
                    200,
                    {"ok": True, "user": user, "token": tok},
                    extra_headers=[
                        ("Set-Cookie", f"{SESSION_COOKIE}={tok}; Path=/; HttpOnly; SameSite=Lax"),
                    ],
                )
            return

        if path == "/api/auth/logout":
            tok = self._session_token()
            with DATA_LOCK:
                uid = SESSIONS.pop(tok, None)
                if uid:
                    auth.log_event(uid, table="users", record_id=uid, note="Signed out")
            self._send_json(
                200,
                {"ok": True},
                extra_headers=[("Set-Cookie", f"{SESSION_COOKIE}=; Path=/; Max-Age=0; HttpOnly; SameSite=Lax")],
            )
            return

        if path == "/api/projects":
            user = self._require_user()
            if not user:
                return
            with DATA_LOCK:
                ok, msg, pid = projects.create_project(
                    str(body.get("name") or ""),
                    str(body.get("description") or ""),
                    user,
                    target_region=str(body.get("target_region") or "Pan-India"),
                )
                if not ok:
                    self._send_json(400, {"error": msg})
                    return
                self._send_json(201, {"ok": True, "message": msg, "project_id": pid})
            return

        if path.startswith("/api/projects/") and path.endswith("/chats/clear"):
            user = self._require_user()
            if not user:
                return
            pid = path.split("/")[3]
            with DATA_LOCK:
                proj = projects.get_project(pid)
                if not proj or not access.can_view(proj, user):
                    self._send_json(403, {"error": "Project access denied."})
                    return
                chats.clear_messages(pid)
                self._send_json(200, {"ok": True, "messages": []})
            return

        if path.startswith("/api/projects/") and path.endswith("/region"):
            user = self._require_user()
            if not user:
                return
            pid = path.split("/")[3]
            with DATA_LOCK:
                proj = projects.get_project(pid)
                if not proj or not access.can_view(proj, user):
                    self._send_json(403, {"error": "Project access denied."})
                    return
                ok, msg, reg = projects.update_project_region(pid, str(body.get("target_region") or "Pan-India"), user)
                if not ok:
                    self._send_json(400, {"error": msg})
                    return
                items = _parse_items(body.get("items"))
                self._send_json(200, {"ok": True, "message": msg, "target_region": reg, "computed": _compute_payload(items, reg) if items else _compute_payload([], reg)})
            return

        if path == "/api/studio/compute":
            user = self._require_user()
            if not user:
                return
            raw_items = _parse_items(body.get("items"))
            validate = bool(body.get("validate", True))
            req_region = str(body.get("target_region") or "Pan-India")
            with DATA_LOCK:
                if not raw_items:
                    self._send_json(200, {"ok": True, "notes": [], "computed": _compute_payload([], req_region)})
                    return
                if validate:
                    ok, validated, notes = formulations.validate_items(raw_items)
                    if not ok:
                        self._send_json(400, {"error": "; ".join(notes), "notes": notes})
                        return
                    self._send_json(200, {"ok": True, "notes": notes, "computed": _compute_payload(validated, req_region)})
                else:
                    self._send_json(200, {"ok": True, "notes": [], "computed": _compute_payload(raw_items, req_region)})
            return

        if path == "/api/studio/chat":
            user = self._require_user()
            if not user:
                return
            pid = str(body.get("project_id") or "")
            instruction = str(body.get("instruction") or "").strip()
            mode = str(body.get("mode") or "formulation").strip()
            constraints = [str(c).strip() for c in (body.get("constraints") or []) if str(c).strip()]
            model = str(body.get("model") or "").strip() or None
            history = body.get("history") if isinstance(body.get("history"), list) else []
            items = _parse_items(body.get("items"))
            explicit_region = str(body.get("target_region") or "").strip()

            with DATA_LOCK:
                proj = projects.get_project(pid) if pid else None
                if pid and (not proj or not access.can_view(proj, user)):
                    self._send_json(403, {"error": "Project access denied."})
                    return
                pname = proj["name"] if proj else "Custom formulation"
                pdesc = proj.get("description", "") if proj else ""
                proj_region = explicit_region or (proj.get("target_region") if proj else "") or "Pan-India"

            mode_prefix = f"[Studio Mode: {mode}]"
            if constraints:
                mode_prefix += f" [Active constraints: {', '.join(constraints)}]"
            full_instruction = f"{mode_prefix} {instruction}".strip() if instruction else ""

            db_ctx = copilot.prepare_db_context(
                full_instruction or instruction,
                project_name=pname,
                project_description=pdesc,
                target_region=proj_region,
            )
            answer = copilot.chat(
                items,
                full_instruction or instruction,
                project_name=pname,
                project_description=pdesc,
                target_region=str(db_ctx.get("target_region") or proj_region),
                db_brief=str(db_ctx["summary"]),
                history=history,
                model=model,
            )
            resolved_reg = str(answer.get("target_region") or db_ctx.get("target_region") or proj_region)
            final_items = answer.get("items") or items
            with DATA_LOCK:
                computed = _compute_payload(final_items, resolved_reg) if final_items else _compute_payload([], resolved_reg)
                saved_messages = chats.append_turn(pid, instruction, answer, user_id=user["user_id"]) if (pid and instruction) else []
            self._send_json(
                200,
                {
                    "ok": True,
                    "reply": answer["reply"],
                    "items_changed": bool(answer.get("items")),
                    "engine": answer["engine"],
                    "requested_model": answer.get("requested_model") or "",
                    "fallback_reason": answer.get("fallback_reason") or "",
                    "status": gemini.status_label(model),
                    "target_region": resolved_reg,
                    "notes": answer.get("notes") or [],
                    "thought": answer.get("thought") or "",
                    "thought_summary": answer.get("thought_summary") or "",
                    "db_crop_count": db_ctx["crop_count"],
                    "computed": computed,
                    "messages": saved_messages,
                },
            )
            return

        if path == "/api/studio/draft":
            user = self._require_user()
            if not user:
                return
            brief = str(body.get("brief") or "").strip()
            cook = str(body.get("cook") or "Baked snack").strip()
            pname = str(body.get("project_name") or "").strip()
            model = str(body.get("model") or "").strip() or None
            if len(brief) < 8:
                self._send_json(400, {"error": "Write a brief description of at least 8 characters."})
                return
            res = copilot.draft(brief, project_name=pname, cook=cook, model=model)
            if not res.get("ok"):
                self._send_json(400, {"error": res.get("reason") or "Could not draft formulation."})
                return
            with DATA_LOCK:
                computed = _compute_payload(res["items"])
            self._send_json(
                200,
                {
                    "ok": True,
                    "name": res["name"],
                    "rationale": res["rationale"],
                    "engine": res["engine"],
                    "status": gemini.status_label(model),
                    "notes": res["notes"],
                    "computed": computed,
                },
            )
            return

        if path == "/api/studio/explain":
            user = self._require_user()
            if not user:
                return
            kind = str(body.get("kind") or "blend")
            items = _parse_items(body.get("items"))
            model = str(body.get("model") or "").strip() or None
            if not items:
                self._send_json(400, {"error": "No formulation items to explain."})
                return
            try:
                if kind == "clean_label":
                    resolved = formulations.resolve(items)
                    findings = cleanlabel.check(resolved)
                    if not findings:
                        self._send_json(200, {"ok": True, "text": "No additive flags exist in the current formulation.", "status": gemini.status_label(model)})
                        return
                    text = copilot.explain_clean_label(findings, model=model)
                else:
                    text = copilot.explain_blend(items, model=model)
                self._send_json(200, {"ok": True, "text": text, "status": gemini.status_label(model)})
            except gemini.GeminiError as exc:
                self._send_json(503, {"error": str(exc)})
            return

        if path == "/api/studio/save":
            user = self._require_user()
            if not user:
                return
            pid = str(body.get("project_id") or "")
            items = _parse_items(body.get("items"))
            name = str(body.get("name") or "").strip()
            notes = str(body.get("notes") or "").strip()
            with DATA_LOCK:
                proj = projects.get_project(pid)
                if not proj or not access.can_view(proj, user):
                    self._send_json(403, {"error": "Project not found or access denied."})
                    return
                ok, msg, fid = formulations.save_project_formulation(
                    project_id=pid,
                    items=items,
                    user_id=user["user_id"],
                    name=name,
                    notes=notes,
                )
                if not ok:
                    self._send_json(400, {"error": msg})
                    return
                self._send_json(200, {"ok": True, "message": msg, "formulation_id": fid})
            return

        if path == "/api/studio/export":
            user = self._require_user()
            if not user:
                return
            pid = str(body.get("project_id") or "")
            items = _parse_items(body.get("items"))
            with DATA_LOCK:
                proj = projects.get_project(pid) if pid else {"project_id": "CUSTOM", "lab_id": user["lab_id"], "name": str(body.get("title") or "Untitled Blueprint"), "description": ""}
                if pid and (not proj or not access.can_view(proj, user)):
                    self._send_json(403, {"error": "Project access denied."})
                    return
                resolved = formulations.resolve(items)
                if not resolved:
                    self._send_json(400, {"error": "Cannot export an empty formulation."})
                    return
                blend = nutrition.blend_nutrition(resolved)
                cost = nutrition.cost_per_kg(resolved)
                base_cost = nutrition.cost_per_kg(formulations.reference_base())
                scost = nutrition.cost_per_serving(resolved)
                findings = cleanlabel.check(resolved)
                latest_meta, _ = formulations.get_latest_project_formulation(pid) if pid else (None, [])
                md = formulations.build_lab_spec_sheet(
                    proj, resolved, blend, cost, base_cost, scost, findings, latest_meta
                )
                self._send_json(200, {"ok": True, "markdown": md, "filename": f"{proj.get('project_id', 'spec')}_lab_spec.md"})
            return

        if path == "/api/ingredients":
            user = self._require_user()
            if not user:
                return
            with DATA_LOCK:
                ok, msg, created = ingredients.create_ingredient(body, user["user_id"])
                if not ok:
                    self._send_json(400, {"error": msg})
                    return
                self._send_json(201, {"ok": True, "message": msg, "ingredient": _serialize_ingredient(created)})
            return

        if path.startswith("/api/ingredients/") and path.endswith("/photo"):
            user = self._require_user()
            if not user:
                return
            iid = path.split("/")[3]
            with DATA_LOCK:
                if body.get("remove"):
                    ok, msg = ingredients.delete_photo(iid, user["user_id"])
                    updated = ingredients.get_ingredient(iid)
                    self._send_json(200, {"ok": ok, "message": msg, "ingredient": _serialize_ingredient(updated) if updated else None})
                    return
                if not body.get("image_b64") or not body.get("filename"):
                    self._send_json(400, {"error": "No image payload supplied."})
                    return
                try:
                    raw_bytes = base64.b64decode(str(body["image_b64"]))
                except Exception:
                    self._send_json(400, {"error": "Invalid image encoding."})
                    return
                ok, msg = ingredients.save_photo(iid, str(body["filename"]), raw_bytes, user["user_id"])
                if not ok:
                    self._send_json(400, {"error": msg})
                    return
                updated = ingredients.get_ingredient(iid)
                self._send_json(200, {"ok": True, "message": msg, "ingredient": _serialize_ingredient(updated) if updated else None})
            return

        if path.startswith("/api/ingredients/") and path.endswith("/verify"):
            user = self._require_admin()
            if not user:
                return
            iid = path.split("/")[3]
            with DATA_LOCK:
                values = body.get("values") if isinstance(body.get("values"), dict) else {}
                nut_conf = str(body.get("nutrition_confidence") or "estimated")
                cost_conf = str(body.get("cost_confidence") or "estimated")
                reference = str(body.get("reference") or "")
                lab_report_rel = ""
                if body.get("report_b64") and body.get("report_name"):
                    try:
                        raw_bytes = base64.b64decode(str(body["report_b64"]))
                        lab_report_rel = auth.save_lab_report(raw_bytes, str(body["report_name"]), iid)
                    except Exception:
                        self._send_json(400, {"error": "Invalid uploaded lab report encoding."})
                        return
                ok, msg = ingredients.save_verification(
                    iid,
                    values=values,
                    nutrition_confidence=nut_conf,
                    cost_confidence=cost_conf,
                    actor_id=user["user_id"],
                    reference=reference,
                    lab_report=lab_report_rel,
                )
                if not ok:
                    self._send_json(400, {"error": msg})
                    return
                updated = ingredients.get_ingredient(iid)
                self._send_json(200, {"ok": True, "message": msg, "ingredient": _serialize_ingredient(updated) if updated else None})
            return

        if path == "/api/admin/users":
            user = self._require_admin()
            if not user:
                return
            with DATA_LOCK:
                ok, msg = auth.create_worker(
                    str(body.get("name") or ""),
                    str(body.get("email") or ""),
                    str(body.get("password") or ""),
                    actor_id=user["user_id"],
                )
                if not ok:
                    self._send_json(400, {"error": msg})
                    return
                self._send_json(201, {"ok": True, "message": msg})
            return

        if path.startswith("/api/admin/users/") and path.endswith("/toggle"):
            user = self._require_admin()
            if not user:
                return
            uid = path.split("/")[4]
            active = bool(body.get("active"))
            with DATA_LOCK:
                ok, msg = auth.set_active(uid, active, actor_id=user["user_id"])
                if not ok:
                    self._send_json(400, {"error": msg})
                    return
                self._send_json(200, {"ok": True, "message": msg})
            return

        if path == "/api/admin/access":
            user = self._require_admin()
            if not user:
                return
            pid = str(body.get("project_id") or "")
            uid = str(body.get("user_id") or "")
            grant_mode = bool(body.get("grant"))
            with DATA_LOCK:
                proj = projects.get_project(pid)
                pname = proj["name"] if proj else ""
                if grant_mode:
                    ok, msg = access.grant(pid, uid, actor_id=user["user_id"], project_name=pname)
                else:
                    ok, msg = access.revoke(pid, uid, actor_id=user["user_id"], project_name=pname)
                if not ok:
                    self._send_json(400, {"error": msg})
                    return
                self._send_json(200, {"ok": True, "message": msg})
            return

        self._send_json(404, {"error": "Unknown API endpoint."})


def main() -> None:
    parser = argparse.ArgumentParser(description="SmartCrop.AI Hybrid Web Server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    _bootstrap_all()
    httpd = ThreadingHTTPServer((args.host, args.port), SmartCropHandler)
    print(f"SmartCrop.AI Web server listening on http://{args.host}:{args.port}", flush=True)
    httpd.serve_forever()


if __name__ == "__main__":
    main()
