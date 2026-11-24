# SmartCrop.AI — Chat Handoff for Antigravity

This file summarizes the Freebuff/Buffy chat context for the SmartCrop.AI project so Antigravity has the project state, decisions, and recent changes.

## Project

**SmartCrop.AI** — Streamlit + Python demo for **HIMOVATION 2026**.  
Goal: a clean-label plant-based formulation co-pilot. Users create formulation projects, see ingredient/nutrition/cost/clean-label panels, and try what-if changes. Outputs are **starting points that need lab validation**.

## Owner Requirements / Constraints

- Build **one milestone at a time**; explain in plain language for a non-coder owner; tell them how to run and what they should see; wait for “go”.
- Local demo accounts only (1 admin + 2 workers), demo-grade auth; admin can grant/revoke per-project visibility.
- Nutrition/cost computed in **Python from DB/CSV values**; Gemini never does arithmetic; every output labelled “starting point, needs lab validation”.
- Gemini key in `.env` only; use `py`/venv python, never `python`.
- Look: Claude/ChatGPT-style warm off-white, near-black, brick accent, thin borders, serif headings, no gradients, no emoji icons.
- Do not deploy; no unrequested features.
- **Gemini/M6 deferred by owner**: “Skip the Gemini integration part for now. It is the most difficult and important part.”
- What-if should be an AI-chat-window **frontend frame only** for now; no AI backend connected yet.
- Validation card removed; simple disclaimer written at top.

## Demo Accounts

| Role | Email | Password | Lab |
|---|---|---|---|
| Lab admin | paras@smartcrop.ai | Admin@123 | LAB-001 SmartCrop Demo Lab |
| Lab worker | shivam@smartcrop.ai | Worker@123 | LAB-001 |
| Lab worker | shreyshi@smartcrop.ai | Worker@123 | LAB-001 |

## How to Run

```powershell
# Windows
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

App: http://localhost:8501. `run.bat` works after `.venv` exists.  
Reset demo data: delete `data/` and reload (app reseeds).

## Milestone / Feature State

### Completed
- **M0/M1**: Streamlit app, sign-in, seeded accounts/lab, admin adds/deactivates workers, worker blocked from Lab admin, audit CSV. Deactivation kills live session (~5s).
- **M2**: Home page with hero, project composer, chips, project cards; sidebar project list; Claude-style theme in `ui.py` + `.streamlit/config.toml`.
- **M3**: Workbench shell (`pages/2_Project.py`) — formulation, what-if, nutrition, cost, clean-label panels.
- **Access control**: `access.py` + `data/project_access.csv`; Lab admin “Project access” grant/revoke; admins see all lab projects, creator always sees own, others need grant; workbench denies unauthorized active project.
- **M4**: Ingredient DB seeded from `data/ingredients.csv` (17 crops, ING-001…ING-017) and `data/sources.csv`; workbench table reads DB names/local names/prices/confidence tags (`unknown` for guar gum).
- **M5**: `nutrition.py` computes blend nutrition/cost in Python — `blend_nutrition`, `cost_per_kg`, `cost_per_serving` (40 g), `confidence_counts`. Baseline = `formulations.reference_base()` (wheat-atta snack, ₹43.91/kg), so blend can be above baseline (honest). Verified arithmetic against hand calculation.
- **M7**: `cleanlabel.py` + `data/additives.csv` (12 terms); additive check panel; soy flour can be `check` (hexane) showing “1 to confirm”.
- **M8-as-chat (frontend frame, no AI)**: `whatif.py` deterministic keyword rule engine; chat UI in workbench “What if” panel. Presets replaced by chat bubbles/composer/Send. Clearly labelled “Prototype replies from local rules — the language model is not connected yet.” Recipe/chat state is session-only (`recipe_{project_id}`, `chat_{project_id}`).
- **Formulation Persistence & Lab Export (Option A)**: `data/formulations.csv` and `data/formulation_items.csv` added with versioning. Workbench now includes "Save Formulation" (persists to CSV), "Export Lab Sheet" (downloads complete Markdown lab validation spec sheet), and "Reset Starter". Saved formulations persist across browser reloads.
- **Validation card removed**: replaced by one disclaimer line under workbench subtitle.
- **Entrance animations**: subtle fade-in + 10px slide-up, 0.45s, `cubic-bezier(0.22, 1, 0.36, 1)` ease-out, staggered delays; `prefers-reduced-motion: reduce` disables. Sidebar intentionally not animated.
- **Lab Admin jitter fix**: Lab admin sections wrapped in keyed containers and animated with a quicker stagger. Main/sidebar scrollbar gutter reserved (`scrollbar-gutter: stable`).

### Deferred / Not Built
- **M6 Gemini integration** — intentionally deferred by owner. Do not build AI calls until asked. `whatif.py` is the local placeholder to replace/integrate later.
- **M9** candidate (not requested as next): admin verification, audit log UI, save/compare/export.
- Per-project formulation persistence not implemented; recipe/chat reset on reload.

## Key Files

| File | Purpose |
|---|---|
| `app.py` | Entry; `st.navigation` (Home, Workbench, Lab admin); sidebar project list; bootstraps auth/projects/ingredients/cleanlabel. |
| `ui.py` | All CSS/theme/motion. Contains entrance animation keyframes, stagger delays, reduced-motion rule, scrollbar-gutter fix. |
| `pages/0_Sign_in.py` | Styled sign-in page. |
| `pages/1_Home.py` | Hero, composer, chips, project cards, access-filtered list. |
| `pages/2_Project.py` | Workbench: header+disclaimer, formulation table from DB, what-if chat, nutrition/cost/clean-label panels. No validation card. |
| `pages/4_Lab_admin.py` | Worker management + Project access grant/revoke; sections keyed for animation. |
| `auth.py` | Demo auth, seeded accounts, worker add/deactivate, session checks. |
| `projects.py` | Project CRUD/listing; `list_visible_projects`, `active_project(user)`, `denied_active_project`. |
| `access.py` | Per-project grants: `can_view`, `grant`, `revoke`, `list_grants`. |
| `ingredients.py` | Seeds/reads ingredient DB and sources; cost/confidence helpers. |
| `formulations.py` | Starter/baseline formulations, resolve helpers. |
| `nutrition.py` | Python nutrition/cost calculations; 40g serving. |
| `cleanlabel.py` | Additive/watchlist rule check. |
| `whatif.py` | Deterministic local what-if rules; replace when M6 lands. |
| `storage.py` | CSV/data storage helpers. |
| `knowledge/PROJECT_NOTES.md` | Running project notes/decisions/gotchas. |
| `data/*.csv` | Seed/runtime demo data (users, labs, projects, access, ingredients, sources, additives, audit). |

## Important Gotchas

- Use `./.venv/Scripts/python.exe` (Windows) / venv python; do not use plain `python`.
- Editing imported modules (`ui.py`, `projects.py`, etc.) requires Streamlit server restart; page files often reload on rerun.
- Browser reload starts a new Streamlit session (signed out).
- Recipe/chat state keys: `recipe_{project_id}`, `chat_{project_id}`; session-only, not saved to CSV.
- Console printing `→`/`₹` may fail under cp1252; use `PYTHONIOENCODING=utf-8` for debug prints.
- Data reset: delete `data/` then reload app.
- Repo is not a git repo; nothing committed.
- Streamlit form styling is scoped to `.st-key-composer` / `.st-key-auth-form` to avoid styling every form globally.

## Recent Chat Changes (latest)

1. Added subtle entrance animations across pages (fade + slide up, ease-out, staggered, reduced-motion aware).
2. Fixed Lab Admin animation: wrapped sections in keyed containers and gave them stagger delays.
3. Fixed Lab Admin jitter reported by user:
   - Root cause: main content width changed when scrollbar appeared/disappeared during expander open/collapse.
   - Fix: `html, [data-testid="stMain"], [data-testid="stSidebar"] { scrollbar-gutter: stable; }` in `ui.py`.
   - Also tightened Lab Admin animation to 0.35s with shorter delays.
4. Packaged project as `SmartCrop.AI-antigravity.zip` with README for extraction/opening in Antigravity.

## Suggested Next Step

Await owner sign-off on current UI/animation behavior. If requested next (non-AI): **M9** (admin verification, audit log UI, save/compare/export) or **per-project formulation persistence**. Do **not** start M6 Gemini unless owner explicitly asks.
