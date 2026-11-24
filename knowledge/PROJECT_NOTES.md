# SmartCrop.AI — Project Notes (read this first in any future session)

_Last updated: 2026-11-24 · Status: M0–M5, M7, M8-chat + Formulation Persistence & Export built — local sign-in, 3 seeded accounts,
admin manages workers (deactivation kills a live session within ~5 s), Home has a time-aware
greeting, the lab's project list, project creation, and the sidebar lists the lab's projects. The
workbench (M3) shows formulation/what-if + nutrition/cost layout, seeded crop database (M4) with
nutrition/cost computed in Python (M5), deterministic clean-label check (M7), and full CSV formulation
persistence with versioning and downloadable Markdown lab validation spec sheets (Option A)._

## What this is
A **multi-page Streamlit + Python web app** that turns locally available crops into candidate
clean-label plant-based food formulations, with nutrition and cost computed in Python from a local
database. Google Gemini only reasons and explains. Multiple users sign in; data is scoped to a lab;
each lab keeps its own projects.

Competition: HIMOVATION 2026 Solve-a-Thon, theme "AI For Food Research".
Team: Panchayat of Programmers (Paras Belwal, Shivam, Shreyshi Bijalwan, Gayatri, Priya).

**The owner is not a coder.** Explain in plain language, one milestone at a time, and always tell
them how to run it and what they should see.

## Environment facts (checked 2026-11-24)
- Windows 11 machine, project at `...\local-projects\0aa7d42b-ce0d-4832-b84a-ae119759a20d`.
- **`python` is not usable** on this machine (Microsoft Store app-alias stub). Use **`py`**.
- Only Python **3.14.7** installed; pip 26.2.1 present; **streamlit not installed**; **not a git repo**.
- Shell is Git Bash. Always use `py`, never `python`, in docs and run commands.
- Risk to check at M0: dependency wheels for Python 3.14 (streamlit/pyarrow). If install fails,
  the fix is a Python 3.12/3.13 install, not hacks.

## Owner decisions (2026-11-24) — these override the old open questions
1. **Accounts:** seeded demo accounts, not in-app signup. 3 accounts in `LAB-001`: 1 `lab_admin`
   (paras@smartcrop.ai) + 2 `lab_worker` (shivam@, shreyshi@). Admin can add/deactivate workers
   from Lab admin. Credentials are listed in the Sign in page's "Demo accounts" expander.
2. **Project visibility:** *not* every lab member sees every lab project. The admin grants or
   revokes, per project, which people may see/certify it. **BUILT 2026-11-24** — `access.py` +
   `data/project_access.csv` (project_id, user_id, granted_by, granted_at), with Grant/Revoke
   toggles per person under **Lab admin → Project access**. Rule: lab admins see every project in
   their lab, a project's creator always sees it, everyone else needs a grant. New projects
   therefore start private to their creator + admins (the old lab-wide default is gone).
3. **Auth:** local demo accounts only (`hashlib.scrypt` in `data/users.csv`). No Google sign-in.
   Must be described to judges as demo auth, not production security.

## Source documents
- `docs/competition_ppt.txt` — competition PPT (problem, feasibility, risks, strategies).
- `docs/team_document.txt` — team solution doc (features, example journey, USPs).
- Originals also in `.cloud-attachments/` (the user calls them "/docs").

## Non-negotiable rules
1. **Nutrition and cost are computed in Python from database values.** Gemini never does arithmetic.
2. **Every output is labelled "starting point, needs lab validation."** AI estimates are never
   presented as verified facts.
3. **Gemini API key lives in `.env` only** (never in code; `.env` gitignored, `.env.example` blank).
4. **One milestone at a time**, then stop, tell the user how to run it and what they should see,
   and **wait for their "go"** before the next.
5. Every database value carries `verified` / `estimated` / `unknown` **plus a source**.

## Navigation architecture (decided 2026-11-24)
`app.py` entry point uses `st.navigation` / `st.Page` (Streamlit ≥1.36 style), wrapped in one auth
gate. `st.set_page_config(layout="wide")`. Sidebar is the navigation + the project list.
**Skeleton-first / text-first build:** every page must be fully navigable and runnable before any
CSS or visual polish. Styling is frozen out of scope until the skeleton milestone is signed off.

Page map:
| Page | File | Roles | Purpose |
|---|---|---|---|
| Sign in | `pages/0_Sign_in.py` | public | Email + password; demo accounts seeded on first run (no signup form) |
| Home | `pages/1_Home.py` | all | Time-aware greeting, lab project list, create project |
| Project workbench | `pages/2_Project.py` | all (lab-scoped) | Left: formulation + what-if. Right: nutrition + cost |
| Crop database | `pages/3_Ingredients.py` | all read; admin edit | Region-filtered ingredient explorer, confidence tags |
| Lab admin | `pages/4_Lab_admin.py` | lab_admin only | Manage workers, verify data, audit log |

## Roles & permissions
- Roles: `lab_admin`, `lab_worker`. Users belong to a `lab_id`.
- Both roles: sign in, see their lab's projects, edit a formulation, run what-if, save.
- Admin only: create/deactivate users, edit ingredient rows, mark values verified, edit project
  metadata, delete projects.
- Visibility rule: a user sees only projects of **their own lab** (matches the PPT's
  "only for their labs").
- Auth is **local demo auth** (users.csv + salted password hashes via stdlib `hashlib.scrypt`,
  session in `st.session_state`). It is NOT production security and must be described as such.
  A real identity provider is a later milestone, not a demo requirement.

## Shared modules
- `storage.py` — CSV read/write, `now()`, `next_sequential_id()` for `U-`/`P-` ids.
- `projects.py` — project storage, `create_project`, access-filtered listing
  (`list_visible_projects`) and active-project selection (`active_project`, plus
  `denied_active_project` so the workbench can explain a revoked selection).
- `ingredients.py` — ingredient/source CSVs, `list_ingredients`, `get_ingredient`,
  `cost_per_100g`, `number()`.
- `formulations.py` — `starter_formulation()` joins the starter recipe to the ingredient DB;
  `reference_base()` is the wheat-atta comparison recipe; `total_share()`.
- `whatif.py` — the what-if chat's local prototype: `RULES`, `apply(items, text)`, `_move`,
  `_reply`; returns (items, reply, changed).
- `cleanlabel.py` — watchlist CSV, `watchlist()`, `check(rows)`; the clean-label rulebook.
- `nutrition.py` — the only place blend numbers are computed: `blend_nutrition`,
  `cost_per_kg`, `cost_per_serving`, `confidence_counts`, `NUTRIENT_ROWS` (label/unit/decimals),
  `SERVING_GRAMS = 40`.
- `access.py` — per-project grants: `can_view`, `grant`, `revoke`, `list_grants`.
  Every page that lists or opens a project goes through it, so revoking a grant removes the
  project from the sidebar and Home on the next rerun and closes the workbench.
- Session rule: `auth.refresh_session_user()` runs on **every** app run and drops a session whose
  account is gone or `active != yes`; `watch_account` (a `st.fragment(run_every=5)`) catches the
  idle case. Streamlit has no push, so ~5 s is the floor; anything faster needs polling.

## Data files (all in `data/`, CSV)
`labs.csv` `users.csv` `projects.csv` `ingredients.csv` `products.csv` `regions.csv`
`replacements.csv` `formulations.csv` `formulation_items.csv` `sources.csv` `project_access.csv`
`additives.csv` `audit_log.csv`

Key fields kept from the first plan: ingredient nutrition per 100 g as-is basis with
`nutrition_basis`, separate `nutrition_confidence` and `cost_confidence`, `cost_basis` with date,
`is_clean_label` + note, `max_practical_pct`, `sources.csv` FK. `audit_log.csv` records logins,
edits, verifications and generated formulations (table, record, field, old, new, by, at).

## Milestone plan (skeleton-first, page by page)
- M0 Skeleton + sign-in shell: app runs, sign-in page renders, first-run admin creation, bad-password
  error, greeting on Home after login. **Gate: verify dependencies install on this Python.**
  **DONE** — `streamlit` installs and runs on Python 3.14.7 in `.venv`.
- M1 Users & labs: admin adds a worker; that worker signs in; worker cannot reach Lab admin.
  **DONE** — `data/users.csv` + `auth.create_worker` + Lab admin page.
- M2 Home + project list: create a project, it appears in the sidebar, greeting is time-aware.
  **DONE** — `projects.csv` (project_id, lab_id, name, description, created_by, created_at,
  updated_at), one shared `data/projects.csv` filtered by `lab_id`; sidebar lists the lab's projects and the selected
  one is marked "•" (`st.session_state["active_project_id"]`, ready for M3).
  Home shows a time-aware serif greeting, a composer card to create a project, three suggestion
  chips that pre-fill the composer, and project cards (name, description, creator, date, id) with a
  Select/Selected pill; the old roadmap list is gone. The card Select button sets the active project
  (same as the sidebar) — it is a no-op without an explicit click handler, so keep that in mind for
  the M3 workbench buttons.
- M3 Project page shell: two-column layout, formulation table and panels render with placeholder
  data, buttons present but inert. **Gate: layout signed off (this is the Antigravity handoff point).**
  **BUILT, awaiting sign-off** — `pages/2_Project.py` (nav title "Workbench") requires an active
  project and otherwise shows an empty state pointing back to Home. Left: formulation table
  (ingredient, share, ₹/100 g, confidence tag) + what-if preset buttons. Right: nutrition rows,
  cost card (₹/kg, baseline delta, per-serving) and a validation card. All figures are placeholder
  constants in the page; the buttons are inert. Shared `ui.py` classes: `wb-*`, `panel_*` panels,
  `.f-table`, `.conf-*`, `.stat-row`, `.cost-*`.
- M4 Real crop data: ingredient explorer + project table read seeded CSVs; confidence tags visible.
  **PARTLY BUILT** — `ingredients.py` seeds `data/ingredients.csv` (17 crops: millets, legumes,
  pulses, cereals, jaggery, guar gum, salt, SMP, groundnut, sesame) and `data/sources.csv` (3
  sources), each row carrying nutrition per 100 g as-is, `nutrition_basis`, separate
  `nutrition_confidence` and `cost_confidence`, cost per kg with `cost_basis`/`cost_date`,
  clean-label flag/note, `max_practical_pct` and a source id. `formulations.py` holds the starter
  base recipe (6 items, 100 %); the workbench resolves it against the DB and shows the local
  name, the DB price per 100 g and the confidence tag, including `unknown` for guar gum fibre.
  **Still to do: the Crop database explorer page (`pages/3_Ingredients.py`)** — not requested yet.
  Blend nutrition/cost remain M5 sample values.
- M5 Maths end-to-end: nutrition right panel + cost vs baseline computed in Python. No AI.
  **BUILT** — `nutrition.py` holds all blend arithmetic: `blend_nutrition` (weighted sum per
  100 g), `cost_per_kg` (ingredient cost of 1 kg), `cost_per_serving` (40 g), and
  `confidence_counts`. Workbench panels now read it: 345 kcal / 18.5 g protein / 2.8 g fat /
  62.7 g carbs / 11.7 g fibre, ₹61.93 per kg, ₹2.48 per 40 g serving, and **41 % ABOVE** the
  reference base (₹43.91/kg), not below. The baseline is `formulations.reference_base()`, a plain
  wheat-atta snack costed from the same ingredient table — a like-for-like reference recipe, not
  a market price. The delta pill turns amber when the blend is dearer.
- M6 Gemini formulation generator behind the validation gate (real ids, % totals 100, caps).
  **DEFERRED by the owner (2026-11-24)** — it is the hardest, most important piece; do not build
  it, or any other AI call, until the owner explicitly asks.
- M7 Clean-label detector + natural replacements.
  **BUILT** — `cleanlabel.py` + hand-written `data/additives.csv` watchlist (12 synthetic terms,
  each with a category, a reason and an optional natural replacement ingredient id + note).
  `check(rows)` matches an ingredient's name/note against the watchlist and also honours the
  ingredient's own `is_clean_label` flag (`yes` / `check` / `no`), returning `flagged` or
  `review` findings. The workbench shows a **Clean label → Additive check** panel with a verdict
  pill (clean / n to confirm / n flagged), the reason per item and, where the watchlist names
  one, the natural option with its DB price. Current starter base: `1 to confirm` (defatted soy
  flour is hexane-extracted; supplier residue spec). Detection is text matching only — never an
  LLM judgement. Swapping an ingredient in the recipe is not wired yet.
- M8 What-if presets on the project page with before/after diff.
  **BUILT as a chat, 2026-11-24** — the preset buttons were replaced at the owner's request by a
  chat window in the left column (Claude-style bubbles + a one-line composer, Enter or Send).
  `whatif.py` is a labelled prototype stand-in for the AI: fixed keyword rules move shares (e.g.
  "more protein" takes 8 points from rice into soy), shares always total 100 %, and the reply
  quotes the real before → after protein/energy/cost. Unknown instructions get an honest "local
  rules, model not connected" reply and change nothing. Recipe and chat live in session state keyed
  by project id, so they reset on reload and never touch the CSVs. **No AI is called.** When M6
  lands, `whatif.apply` is the function to replace with the model call.
- M9 Admin verification + audit log + save/compare/export.

## Visual direction — NOW IMPLEMENTED (owner asked for a Claude/ChatGPT-style homepage, 2026-11-24)
The style freeze is lifted for Home + sign in. Palette lives in `.streamlit/config.toml` (base
light, `primaryColor #c2603c`, `backgroundColor #faf9f5`, `secondaryBackgroundColor #f2f0e8`,
`textColor #22201c`) so Streamlit's own widgets follow it; shapes and typography accents live in
`ui.py` (`apply_theme()`, called once in `app.py`). Home = centered hero (serif display heading,
role/lab eyebrow, one-line subtitle), a rounded composer card for creating a project (two borderless
inputs + brick CTA + validation hint), three suggestion chips that pre-fill the composer, then
project cards with a Select/Selected pill. **Entrance motion (2026-11-24):** one keyframe, `rise-in` (opacity 0 → 1, translateY 10 px → 0),
0.45 s with `cubic-bezier(0.22, 1, 0.36, 1)` (ease-out), applied once per element with `both` fill.
Targets: hero / auth hero, Home composer and chips, section headings, project cards, workbench
header and all `panel_*` cards, alerts. Lab admin has no cards, so each section is wrapped in a
keyed container (`admin_head` / `admin_add` / `admin_people` / `admin_access`) and animates in
that order (20 / 80 / 160 / 240 ms). Sidebar deliberately not animated. Delays stagger from 0 to 250 ms. Sidebar deliberately not
animated. `prefers-reduced-motion: reduce` switches it all off. Streamlit keeps keyed containers
alive across reruns, so sending a chat message does not replay the whole page; the animation is
CSS-only, no JS.

**UI change 2026-11-24:** the standalone Validation card is gone; its one-line disclaimer now sits
under the workbench subtitle (`.wb-disclaimer`, brick hairline). Form-card styling is now scoped
with `.st-key-composer` / `.st-key-auth-form`, so the chat composer needs its own rules under
`[class*="st-key-panel_whatif"]`.

**Gotchas learned:** a wide HTML table inside a panel overflows the card unless `.f-table` uses
`table-layout: fixed` with explicit `nth-child` widths; form-submit buttons are
`data-testid="stBaseButton-primaryFormSubmit"` (not `stBaseButton-primary`); Streamlit's heading
rules beat a plain class, so custom type needs `!important`; a widget's session value cannot be set
after it is drawn, so chips bump a `draft_version` that re-keys the input; the preview panel is
only ~600 px wide unless resized, which makes the sidebar overlay content.

**Rules that still apply:** modern and clean SaaS like Linear or Notion: warm off-white canvas, near-black text, brick/ochre
accent, generous whitespace, thin borders, one accent colour, no gradients, no emoji as icons.
Sidebar on the left for both navigation and project switching.

## Open questions for the user
1. ~~Accounts~~ — answered: seeded demo accounts (see Owner decisions).
2. ~~Visibility~~ — answered: admin grants project access per person (see Owner decisions).
3. ~~Login type~~ — answered: local demo accounts.
4. Demo deadline and presentation machine (own laptop vs venue)?
5. Real data sources (IFCT 2017, mandi prices, lab measurements) vs seeded estimates?
6. Lab-admin database editing in the demo, or later?
7. ~~What-if as preset buttons or free-text chat?~~ — answered: free-text chat window (built, M8).
8. Are the four goal scores computed by formula in code, with texture labelled an AI estimate?

## Known data gaps (resolve before data entry)
- **Seeded crop values are approximate public reference ranges, all marked `estimated`** (one
  `unknown`) — they must be replaced with IFCT 2017 transcriptions or lab measurements before the
  demo claims them as fact. Costs are a single-day team spot survey (`2026-11-20`), no invoices.
Nutrition basis (as-is vs dry, and whether water counts toward 100%), cost basis/date, and an
explicit hand-written synthetic-additive list — "clean label" must never be an LLM judgement.
