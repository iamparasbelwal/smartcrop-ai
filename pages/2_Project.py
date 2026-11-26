"""Project workbench: formulation and what-if on the left, nutrition and cost on the right.

M3 shell only: the layout, the panels and every button are in place, but the rows are
placeholder data and the buttons do not change anything yet. Nothing here is saved.
"""

import streamlit as st

import auth
import cleanlabel
import copilot
import formulations
import gemini
import ingredients
import nutrition
import projects
import ui

user = auth.require_login()
ui.mark_active_page("project")
project = projects.active_project(user)

# When no project is selected: keep standard expanded sidebar (240px) and display clean empty state
if project is None:
    denied = projects.denied_active_project(user)
    st.markdown(
        """
        <style>
        [data-testid="stHeaderActionElements"], a.anchor-link, .anchor-link { display: none !important; }
        .st-key-wb_empty_layout { max-width: 940px !important; margin: 0.5rem 0 2rem 0 !important; padding: 0 !important; }
        .wb-empty-header { margin-bottom: 1.8rem; text-align: left; }
        .wb-empty-header .wb-eyebrow { font-size: 0.72rem; letter-spacing: 0.12em; text-transform: uppercase; color: var(--muted); font-weight: 600; margin-bottom: 0.35rem; }
        .wb-empty-header .wb-title { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif !important; font-size: 2.25rem; font-weight: 700; color: var(--ink); margin: 0.2rem 0 0.45rem 0; letter-spacing: -0.025em; line-height: 1.2; }
        .wb-empty-header .wb-desc { font-size: 0.95rem; color: var(--muted); max-width: 640px; margin: 0; line-height: 1.5; }
        </style>
        """,
        unsafe_allow_html=True,
    )
    with st.container(key="wb_empty_layout"):
        if denied is not None:
            st.markdown(
                f'<div class="wb-empty-header">'
                f'<div class="wb-eyebrow">{ui.esc(auth.LAB_NAME)} · ACCESS RESTRICTED</div>'
                f'<div class="wb-title">Access Restricted</div>'
                f'<div class="wb-desc">You do not have access to <strong>{ui.esc(denied["name"])}</strong>. Your lab admin can grant access in <em>Lab admin → Project access</em>.</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div class="wb-empty-header">'
                f'<div class="wb-eyebrow">{ui.esc(auth.LAB_NAME)} · FORMULATION WORKBENCH</div>'
                f'<div class="wb-title">No project selected</div>'
                f'<div class="wb-desc">Choose an active crop formulation below to open its interactive Workbench.</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

        # Quick-select list of available lab projects
        available = projects.list_visible_projects(user)
        if available:
            st.markdown(
                f'<div class="section-row" style="margin-top: 1.4rem; margin-bottom: 0.8rem;">'
                f'<div class="section-title">Your Lab Projects ({len(available)})</div>'
                f'<div class="section-count">Click to open directly into Workbench</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
            for p in available:
                with st.container(border=True, key=f"pcard_{p['project_id']}", vertical_alignment="center"):
                    left, right = st.columns([3.8, 1.4], vertical_alignment="center")
                    with left:
                        desc_text = (
                            f'<div class="card-desc" style="margin: 0.25rem 0 0.35rem 0; font-size: 0.88rem; color: #4c4842; line-height: 1.4;">{ui.esc(p["description"])}</div>'
                            if p.get("description")
                            else '<div class="card-desc" style="margin: 0.25rem 0 0.35rem 0; font-size: 0.86rem; color: var(--muted); font-style: italic;">No description yet.</div>'
                        )
                        st.markdown(
                            f'<div class="project-info-block">'
                            f'<div class="card-title" style="font-size: 1.05rem; margin-bottom: 0.2rem;">{ui.esc(p["name"])}</div>'
                            f'{desc_text}'
                            f'<div class="card-meta" style="color: var(--muted); font-size: 0.74rem;">ID: <code>{ui.esc(p["project_id"])}</code></div>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )
                    with right:
                        if st.button(
                            "Open Workbench →",
                            key=f"quick_open_{p['project_id']}",
                            type="primary",
                            use_container_width=True,
                        ):
                            projects.set_active_project(p["project_id"])
                            st.rerun()

    st.stop()

# Inject Workbench-specific permanently collapsed icon-rail sidebar and full-canvas layout ONLY for active project
WORKBENCH_SIDEBAR_CSS = """
<style>
/* ---------- WORKBENCH-ONLY: Permanently collapsed icon rail sidebar ---------- */
[data-testid="stSidebar"] {
    width: 64px !important;
    min-width: 64px !important;
    max-width: 64px !important;
    position: fixed !important;
    top: 0 !important;
    left: 0 !important;
    bottom: 0 !important;
    height: 100vh !important;
    z-index: 9999999 !important;
    background: var(--sand) !important;
    border-right: 1px solid var(--line) !important;
    overflow: hidden !important;
    overflow-y: hidden !important;
    scrollbar-width: none !important;
    pointer-events: auto !important;
}

/* Ensure Streamlit top header never overlays or intercepts clicks on the 64px sidebar */
header[data-testid="stHeader"] {
    left: 64px !important;
    width: calc(100vw - 64px) !important;
    z-index: 100 !important;
    pointer-events: none !important;
}
header[data-testid="stHeader"] > * {
    pointer-events: auto !important;
}

[data-testid="stSidebar"] [data-testid="stSidebarContent"] {
    width: 64px !important;
    min-width: 64px !important;
    padding: 1.2rem 0 !important;
    box-sizing: border-box !important;
    display: flex !important;
    flex-direction: column !important;
    justify-content: space-between !important;
    pointer-events: auto !important;
}

[data-testid="stSidebarNav"] {
    width: 100% !important;
    padding: 0 !important;
    margin: 0 !important;
    pointer-events: auto !important;
}

[data-testid="stSidebarNav"] ul {
    padding: 0 !important;
    margin: 0 !important;
    list-style: none !important;
}

/* Nav links: fully clickable 44px square centered in the 64px rail */
[data-testid="stSidebarNavLink"] {
    height: 44px !important;
    min-height: 44px !important;
    max-height: 44px !important;
    width: 44px !important;
    margin: 0 auto 6px auto !important;
    padding: 0 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    border-radius: 12px !important;
    box-sizing: border-box !important;
    background: transparent !important;
    text-decoration: none !important;
    cursor: pointer !important;
    pointer-events: auto !important;
    position: relative !important;
    z-index: 10 !important;
    transition: background 0.15s ease !important;
}
[data-testid="stSidebarNavLink"]:hover {
    background: #e9e5d7 !important;
}

/* Make child elements inside link transparent to clicks so click hits the <a> tag */
[data-testid="stSidebarNavLink"] * {
    pointer-events: none !important;
}

/* Dead-centered small icon */
[data-testid="stSidebarNavLink"] span:first-child,
[data-testid="stSidebarNavLink"] [data-testid="stIconMaterial"] {
    font-size: 1.4rem !important;
    width: 44px !important;
    height: 44px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    margin: 0 !important;
    padding: 0 !important;
}

/* Hide text label completely on Workbench */
[data-testid="stSidebarNavLink"] span:last-child:not(:first-child) {
    display: none !important;
}

/* ---------- Centered Bottom Footer (Avatar + Sign-out) ---------- */
.st-key-side_bottom {
    margin-top: auto !important;
    padding-top: 1.1rem !important;
    border-top: 1px solid var(--line) !important;
    display: flex !important;
    flex-direction: column !important;
    align-items: center !important;
    justify-content: center !important;
    width: 64px !important;
    box-sizing: border-box !important;
    pointer-events: auto !important;
    position: relative !important;
    z-index: 10 !important;
}

.side-user-row {
    margin: 0 auto 1.1rem auto !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}

.side-avatar {
    width: 36px !important;
    height: 36px !important;
    border-radius: 50% !important;
    background: #e8e3d5 !important;
    color: var(--ink) !important;
    font-weight: 700 !important;
    font-size: 0.95rem !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    margin: 0 auto !important;
    border: 1px solid var(--line) !important;
}

.side-user-details {
    display: none !important;
}

.st-key-side_bottom [data-testid="stButton"] {
    width: 44px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    margin: 0 auto !important;
    pointer-events: auto !important;
}

.st-key-side_bottom [data-testid="stButton"] button {
    width: 44px !important;
    min-width: 44px !important;
    height: 40px !important;
    padding: 0 !important;
    margin: 0 auto !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    border-radius: 10px !important;
    border: 1px solid var(--line) !important;
    background: var(--panel) !important;
    color: #8a3f26 !important;
    cursor: pointer !important;
    pointer-events: auto !important;
    transition: background 0.15s ease !important;
}

.st-key-side_bottom [data-testid="stButton"] button p {
    display: none !important;
}

/* ---------- FULL-CANVAS UTILIZATION (Zero Wasted Space) ---------- */
[data-testid="stMain"] {
    margin-left: 64px !important;
    width: calc(100vw - 64px) !important;
    max-width: calc(100vw - 64px) !important;
    padding: 0 !important;
}

[data-testid="stMain"] .block-container {
    max-width: 100% !important;
    width: 100% !important;
    padding-left: 1.8rem !important;
    padding-right: 2.2rem !important;
    padding-top: 1rem !important;
    padding-bottom: 2rem !important;
    margin: 0 !important;
}

/* Entrance motion for Workbench project titles */
@keyframes rise-in {
    from { opacity: 0; transform: translate3d(0, 10px, 0); }
    to { opacity: 1; transform: translate3d(0, 0, 0); }
}

.st-key-wb-head,
.st-key-wb_head,
h1.wb-title,
.wb-title,
.wb-eyebrow,
.wb-sub,
.wb-disclaimer {
    animation: rise-in 0.45s cubic-bezier(0.22, 1, 0.36, 1) both;
}

.wb-eyebrow { animation-delay: 20ms; }
h1.wb-title, .wb-title { animation-delay: 60ms; }
.wb-sub { animation-delay: 100ms; }
.wb-disclaimer { animation-delay: 140ms; }
</style>
"""
st.markdown(WORKBENCH_SIDEBAR_CSS, unsafe_allow_html=True)

OPENING_CHAT = [
    {
        "role": "assistant",
        "text": "How can I help you?",
    }
]


def _rows_html(rows: list[dict], blend_cost: float = 0.0) -> str:
    cells = []
    total_share = sum(row["share_pct"] for row in rows)
    for row in rows:
        ingredient = row["ingredient"]
        confidence = ingredient["nutrition_confidence"] or "unknown"
        price = ingredients.cost_per_100g(ingredient)
        name = ui.esc(ingredient["name"])
        local_name = ui.esc(ingredient.get("local_name") or "")
        category = ui.esc(ingredient.get("category") or "Crop")

        local_html = f'<span class="ing-local">{local_name}</span>' if local_name else ""
        cat_badge = f'<span class="cat-tag">{category}</span>'

        # Share percentage with visual proportional bar
        bar_pct = min(100.0, max(2.0, row["share_pct"] * 2.2))
        share_html = (
            f'<div class="share-bar-wrap">'
            f'<div class="share-bar-bg"><div class="share-bar-fill" style="width: {bar_pct:.0f}%;"></div></div>'
            f'<span style="font-weight: 500; min-width: 44px; text-align: right;">{row["share_pct"]:.1f}%</span>'
            f"</div>"
        )

        cells.append(
            "<tr>"
            f"<td><strong>{name}</strong>{local_html}</td>"
            f"<td>{cat_badge}</td>"
            f'<td class="num">{share_html}</td>'
            f'<td class="num" style="font-weight: 500;">₹{price:,.2f}</td>'
            f'<td><span class="conf conf-{ui.esc(confidence)}">{ui.esc(confidence)}</span></td>'
            "</tr>"
        )

    cost_per_100g_blend = (
        blend_cost / 10
        if blend_cost
        else sum(
            ingredients.cost_per_100g(r["ingredient"]) * r["share_pct"] / 100 for r in rows
        )
    )

    tfoot = (
        "<tfoot><tr>"
        "<td><strong>Total Blend</strong></td>"
        f'<td><span class="cat-tag">{len(rows)} crops</span></td>'
        f'<td class="num" style="font-weight: 700;">{total_share:.1f}%</td>'
        f'<td class="num" style="font-weight: 700;">₹{cost_per_100g_blend:,.2f}</td>'
        '<td><span class="conf conf-verified">100% batch</span></td>'
        "</tr></tfoot>"
    )

    return (
        '<table class="f-table">'
        "<thead><tr>"
        '<th style="width: 34%;">Ingredient / Crop</th>'
        '<th style="width: 17%;">Category</th>'
        '<th style="width: 23%; text-align: right;">Share (%)</th>'
        '<th style="width: 14%; text-align: right;">₹/100 g</th>'
        '<th style="width: 12%;">Confidence</th>'
        "</tr></thead>"
        "<tbody>" + "".join(cells) + "</tbody>"
        + tfoot
        + "</table>"
    )


def _nutrition_html(blend: dict[str, float]) -> str:
    return "".join(
        f'<div class="stat-row"><span class="stat-label">{ui.esc(label)}</span>'
        f'<span class="stat-value">{blend[field]:,.{decimals}f}'
        f'<span class="stat-unit">{ui.esc(unit)}</span></span></div>'
        for field, label, unit, decimals in nutrition.NUTRIENT_ROWS
    )


def _clean_label_html(findings: list[dict]) -> str:
    flagged = sum(1 for finding in findings if finding["status"] == "flagged")
    review = len(findings) - flagged
    if flagged:
        verdict, verdict_class = f"{flagged} flagged", "conf conf-flagged"
    elif review:
        verdict, verdict_class = f"{review} to confirm", "conf conf-review"
    else:
        verdict, verdict_class = "clean", "conf conf-verified"

    parts = [f'<div class="cl-verdict"><span class="{verdict_class}">{verdict}</span></div>']
    if not findings:
        parts.append(
            '<div class="panel-note">No synthetic additive from the watchlist in this recipe.</div>'
        )

    for finding in findings:
        ingredient = finding["ingredient"]
        if finding["status"] == "flagged":
            label, badge = "flagged", "conf-flagged"
        else:
            label, badge = "confirm", "conf-review"

        option = finding["option"]
        if option is not None:
            extra = (
                f'<div class="cl-swap">Natural option: {ui.esc(option["name"])} '
                f"(₹{ingredients.cost_per_100g(option):,.2f}/100 g)</div>"
            )
        elif finding["replacement_note"]:
            extra = f'<div class="cl-swap">{ui.esc(finding["replacement_note"])}</div>'
        else:
            extra = ""

        parts.append(
            '<div class="cl-item">'
            f'<div class="cl-head"><span class="cl-name">{ui.esc(ingredient["name"])}</span>'
            f'<span class="conf {badge}">{label}</span></div>'
            f'<div class="cl-why">{ui.esc(finding["why"])}</div>'
            f"{extra}</div>"
        )
    return "".join(parts)


def _compare_html(rows: list[dict], label_a: str, label_b: str) -> str:
    cells = []
    for row in rows:
        ingredient = row["ingredient"]
        delta = row["delta"]
        if abs(delta) < 0.05:
            pill = '<span class="cat-tag">unchanged</span>'
        elif delta > 0:
            pill = f'<span class="conf conf-review">+{delta:.1f}</span>'
        else:
            pill = f'<span class="conf conf-verified">{delta:.1f}</span>'
        cells.append(
            "<tr>"
            f"<td><strong>{ui.esc(ingredient['name'])}</strong></td>"
            f'<td class="num">{row["share_a"]:.1f}%</td>'
            f'<td class="num">{row["share_b"]:.1f}%</td>'
            f"<td>{pill}</td>"
            "</tr>"
        )
    return (
        '<table class="f-table">'
        "<thead><tr><th>Ingredient</th>"
        f'<th style="text-align: right;">{ui.esc(label_a)}</th>'
        f'<th style="text-align: right;">{ui.esc(label_b)}</th>'
        '<th style="width: 24%;">Change</th></tr></thead>'
        "<tbody>" + "".join(cells) + "</tbody></table>"
    )


def _skeleton_spec_html() -> str:
    """Empty formulation wireframe shown before the user prompts Gemini."""
    kpi_labels = ["Cost / kg", "Protein", "Energy", "Clean Label"]
    kpis = "".join(
        f'<div class="skel-kpi-card">'
        f'<div class="kpi-label">{label}</div>'
        f'<div class="skel-bar skel-val"></div>'
        f'<div class="skel-bar skel-sub"></div>'
        f"</div>"
        for label in kpi_labels
    )
    rows = []
    widths = [("68%", "52%"), ("58%", "44%"), ("64%", "48%"), ("50%", "38%"), ("55%", "40%")]
    for idx, (w_name, w_share) in enumerate(widths):
        opacity = max(0.32, 0.92 - idx * 0.14)
        rows.append(
            f'<div class="skel-row" style="opacity: {opacity:.2f};">'
            f'<div class="skel-cell-name"><div class="skel-bar" style="width: {w_name}; height: 11px;"></div>'
            f'<div class="skel-bar" style="width: 34%; height: 8px; margin-top: 5px; opacity: 0.7;"></div></div>'
            f'<div class="skel-cell-cat"><div class="skel-bar" style="width: 58px; height: 18px; border-radius: 999px;"></div></div>'
            f'<div class="skel-cell-share"><div class="skel-bar" style="width: {w_share}; height: 7px;"></div></div>'
            f'<div class="skel-cell-num"><div class="skel-bar" style="width: 42px; height: 10px; margin-left: auto;"></div></div>'
            f"</div>"
        )
    return (
        '<div class="skel-head">'
        '<div>'
        '<div style="font-size: 0.72rem; color: var(--muted); letter-spacing: 0.08em; text-transform: uppercase;">FORMULATION SPEC</div>'
        '<span class="conf conf-estimated">Awaiting goals</span>'
        '</div>'
        '<div class="skel-actions">'
        '<div class="skel-btn-ghost"></div>'
        '<div class="skel-btn-ghost" style="width: 78px;"></div>'
        '</div>'
        '</div>'
        f'<div class="skel-kpi-grid">{kpis}</div>'
        '<div class="skel-tab-bar">'
        '<span class="skel-tab active">Formulation</span>'
        '<span class="skel-tab">Nutrition</span>'
        '<span class="skel-tab">Cost</span>'
        '<span class="skel-tab">Additive Check</span>'
        '<span class="skel-tab">Versions</span>'
        '</div>'
        '<div class="skel-table-head">'
        '<span>Ingredient / Crop</span><span>Category</span><span>Share (%)</span><span style="text-align: right;">₹/100 g</span>'
        '</div>'
        + "".join(rows)
        + '<div class="skel-empty-note">'
        '<strong>No formulation yet</strong><br>'
        'Send us your requirements in the chat, the AI models will do the rest for you.'
        '</div>'
    )


def _chat_html(messages: list[dict], pending_status: str = "") -> str:
    rows = []
    for message in messages:
        role = "me" if message["role"] == "user" else "ai"
        text = ui.esc(message["text"]).replace("\n", "<br>")
        meta = ""
        if role == "ai" and message.get("engine") and message.get("engine") != "SmartCrop co-pilot":
            meta = f'<span class="chat-meta">{ui.esc(message["engine"])}</span>'
        if role == "ai" and message.get("thought"):
            summary_txt = ui.esc(message.get("thought_summary") or "Reviewed crop database & reasoning")
            thought_txt = ui.esc(message["thought"]).replace("\n", "<br>")
            rows.append(
                f'<div class="chat-row ai">'
                f'<div class="ai-thought-wrap">'
                f'<details class="ai-thought">'
                f'<summary><span class="ai-thought-dots"><i></i><i></i><i></i></span>'
                f'<span>{summary_txt}</span><span class="ai-status-chevron">&rsaquo;</span></summary>'
                f'<div class="ai-thought-body">{thought_txt}</div>'
                f'</details>'
                f'<div class="chat-bubble">{text}{meta}</div>'
                f'</div>'
                f'</div>'
            )
        else:
            rows.append(f'<div class="chat-row {role}"><div class="chat-bubble">{text}{meta}</div></div>')
    if pending_status:
        rows.append(ui.status_html(pending_status))
    return f'<div class="chat-log">{"".join(rows)}</div>'


@st.dialog("Draft a formulation with AI", width="large")
def ai_draft_dialog(project_name: str, project_id: str) -> None:
    """M6: a written brief becomes a validated recipe, then a workbench draft."""
    st.markdown(
        '<div class="panel-note" style="margin: 0 0 0.9rem;">Describe the product in ordinary '
        "words. Gemini chooses the crops and their shares from the lab database; SmartCrop then "
        "checks every id, the practical cap on each crop and the 100 % total before any number "
        "reaches the screen.</div>",
        unsafe_allow_html=True,
    )
    brief = st.text_area(
        "What should the product be?",
        key=f"ai_brief_{project_id}",
        height=110,
        placeholder="A high-protein baked snack for school children, as cheap as possible, "
        "at most 8% jaggery...",
    )
    cook = st.selectbox(
        "How is it made?",
        ["Baked snack", "Pan-fried flatbread", "Extruded puff", "No-cook energy mix"],
        key=f"ai_cook_{project_id}",
    )
    if st.button("Draft the recipe", type="primary", use_container_width=True):
        if len(brief.strip()) < 12:
            st.warning("Write a line or two about the product you want.")
        else:
            with st.spinner("Formulating recipe from crop database…"):
                st.session_state["ai_draft_result"] = copilot.draft(
                    brief,
                    project_name=project_name,
                    cook=cook,
                    model=st.session_state.get("workbench_model") or None,
                )
            st.session_state["ai_draft_prompt"] = brief.strip()

    result = st.session_state.get("ai_draft_result")
    if not result:
        return
    if not result.get("ok"):
        st.warning(f"No usable recipe came back — {result.get('reason', 'unknown reason')}")
        return

    st.markdown(
        '<div class="panel-label" style="margin-top: 0.9rem;">PROPOSED PRODUCT</div>'
        f'<div class="panel-title">{ui.esc(result["name"])}</div>'
        f'<div class="panel-note" style="margin-top: 0;">{ui.esc(result["rationale"])}</div>',
        unsafe_allow_html=True,
    )
    st.markdown(_rows_html(formulations.resolve(result["items"])), unsafe_allow_html=True)

    blend = result["blend"]
    st.markdown(
        '<div class="kpi-strip" style="margin-top: 0.9rem;">'
        '<div class="kpi-card"><div class="kpi-label">Cost / kg</div>'
        f'<div class="kpi-value">₹{result["cost"]:,.2f}</div>'
        '<div class="kpi-note">ingredient cost</div></div>'
        '<div class="kpi-card"><div class="kpi-label">Protein</div>'
        f'<div class="kpi-value">{blend["protein_g"]:.1f}g</div>'
        '<div class="kpi-note">per 100 g</div></div>'
        '<div class="kpi-card"><div class="kpi-label">Energy</div>'
        f'<div class="kpi-value">{blend["energy_kcal"]:.0f}</div>'
        '<div class="kpi-note">kcal / 100 g</div></div>'
        "</div>",
        unsafe_allow_html=True,
    )
    notes = result.get("notes") or []
    st.caption(
        "Checks applied: " + "; ".join(notes)
        if notes
        else "All shares passed the id, cap and 100 % checks unchanged."
    )
    st.caption(
        f"Drafted by {result['engine']} from “{st.session_state.get('ai_draft_prompt', '')}”. "
        "A starting point only — the lab still has to measure the batch."
    )
    if st.button("Use this recipe in the workbench", type="primary", use_container_width=True):
        st.session_state[f"recipe_{project_id}"] = result["items"]
        st.session_state[f"chat_{project_id}"] = list(OPENING_CHAT)
        st.session_state.pop(f"explain_{project_id}", None)
        st.session_state.pop("ai_draft_result", None)
        st.session_state[f"save_notice_{project_id}"] = (
            f"Loaded the AI draft “{result['name']}” as an unsaved version. Press Save to keep it."
        )
        st.rerun()


with st.container(key="wb-head"):
    st.markdown(
        f'<div class="wb-eyebrow">{ui.esc(project["project_id"])} · {ui.esc(auth.LAB_NAME)}</div>',
        unsafe_allow_html=True,
    )
    st.markdown(f'<h1 class="wb-title">{ui.esc(project["name"])}</h1>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="wb-sub">{ui.esc(project["description"] or "No description yet.")}</div>'
        '<div class="wb-disclaimer">Starting point, not a result — every figure is an estimate '
        "until the lab measures the batch.</div>",
        unsafe_allow_html=True,
    )

recipe_key = f"recipe_{project['project_id']}"
chat_key = f"chat_{project['project_id']}"

saved_meta, saved_items = formulations.get_latest_project_formulation(project["project_id"])
versions = formulations.list_project_formulations(project["project_id"])
if recipe_key not in st.session_state:
    st.session_state[recipe_key] = saved_items

recipe_items = st.session_state.get(recipe_key) or []
has_formulation = bool(recipe_items)
messages = st.session_state.get(chat_key) or list(OPENING_CHAT)
catalog_size = len(ingredients.list_ingredients())

if has_formulation:
    recipe = formulations.resolve(recipe_items)
    blend = nutrition.blend_nutrition(recipe)
    blend_cost = nutrition.cost_per_kg(recipe)
    baseline_cost = nutrition.cost_per_kg(formulations.reference_base())
    serving_cost = nutrition.cost_per_serving(recipe)
    quality = nutrition.confidence_counts(recipe)
    findings = cleanlabel.check(recipe)

    spec_sheet_md = formulations.build_lab_spec_sheet(
        project=project,
        recipe_rows=recipe,
        blend_nutrition=blend,
        blend_cost=blend_cost,
        baseline_cost=baseline_cost,
        serving_cost=serving_cost,
        findings=findings,
        formulation_meta=saved_meta,
    )

    delta_pct = (blend_cost - baseline_cost) / baseline_cost * 100 if baseline_cost else 0.0
    if abs(delta_pct) < 1:
        delta_text, delta_class = "in line with the reference base", "cost-delta"
    elif delta_pct < 0:
        delta_text, delta_class = f"{abs(delta_pct):.0f}% below the reference base", "cost-delta"
    else:
        delta_text, delta_class = f"{abs(delta_pct):.0f}% above the reference base", "cost-delta up"

save_notice = st.session_state.pop(f"save_notice_{project['project_id']}", "")
if save_notice:
    st.success(save_notice)

left, right = st.columns([1.38, 1.0], gap="large")

model_choices = gemini.model_choices()
model_options = [value for _, value in model_choices]
model_labels = {value: label for label, value in model_choices}
if st.session_state.get("workbench_model") not in model_options:
    st.session_state["workbench_model"] = model_options[0]

with left:
    with st.container(border=True, key="panel_chat"):
        head_left, head_right = st.columns([1.45, 1.0], vertical_alignment="top", gap="small")
        with head_left:
            st.markdown(
                '<div class="panel-label" style="margin-bottom: 0.15rem;">SMARTCROP CO-PILOT</div>'
                '<div class="panel-title" style="margin-bottom: 0;">Formulation assistant</div>',
                unsafe_allow_html=True,
            )
        with head_right:
            selected_model = st.selectbox(
                "AI router model",
                options=model_options,
                format_func=lambda val: model_labels.get(val, val or "Auto"),
                key="workbench_model",
                label_visibility="collapsed",
            )
            st.markdown(
                f'<div class="chat-engine-wrap"><span class="chat-engine">{ui.esc(gemini.status_label(selected_model))}</span></div>',
                unsafe_allow_html=True,
            )
        st.markdown('<div class="chat-header-rule"></div>', unsafe_allow_html=True)
        chat_slot = st.empty()
        chat_slot.markdown(_chat_html(messages), unsafe_allow_html=True)

        st.markdown('<div class="chat-chips-label">Quick prompts</div>', unsafe_allow_html=True)
        prompt_cols = st.columns(4, gap="small")
        if has_formulation:
            prompts = [
                ("More protein", "more protein", ":material/bolt:"),
                ("Lower cost", "lower cost", ":material/trending_down:"),
                ("More millet", "more millet", ":material/grass:"),
                ("Less sugar", "less sweet", ":material/water_drop:"),
            ]
        else:
            prompts = [
                ("High protein", "Create a high-protein formulation from the private crop database for this project goal.", ":material/bolt:"),
                ("Low cost", "Create an affordable, cost-optimized formulation using local crops from the database.", ":material/trending_down:"),
                ("Millet base", "Build a millet-rich clean-label formulation using local crops from the database.", ":material/grass:"),
                ("Low sugar", "Build a low-sugar clean-label plant formulation using ingredients from the database.", ":material/water_drop:"),
            ]
        clicked_prompt = None
        for idx, (pcol, (plabel, pcmd, picon)) in enumerate(zip(prompt_cols, prompts)):
            if pcol.button(
                plabel,
                icon=picon,
                key=f"qp_{'edit' if has_formulation else 'empty'}_{idx}",
                use_container_width=True,
            ):
                clicked_prompt = pcmd

        input_placeholder = "Describe your formulation goals"
        with st.form("workbench_chat_form", clear_on_submit=True, border=False):
            input_column, send_column = st.columns([4.2, 1.2], vertical_alignment="center", gap="small")
            with input_column:
                instruction = st.text_input(
                    "Instruction",
                    key="workbench_chat_input",
                    placeholder=input_placeholder,
                    label_visibility="collapsed",
                )
            with send_column:
                sent = st.form_submit_button("Send ↵", type="primary", use_container_width=True)

        action_instruction = clicked_prompt or (instruction.strip() if sent else None)
        if action_instruction:
            pending_messages = messages + [{"role": "user", "text": action_instruction}]
            chat_slot.markdown(
                _chat_html(
                    pending_messages,
                    pending_status="Searching private crop & additive database",
                ),
                unsafe_allow_html=True,
            )
            db_ctx = copilot.prepare_db_context(
                action_instruction,
                project_name=project["name"],
                project_description=project.get("description", ""),
            )
            chat_slot.markdown(
                _chat_html(
                    pending_messages,
                    pending_status=f"Evaluating {db_ctx['crop_count']} database crops & formulating blend",
                ),
                unsafe_allow_html=True,
            )
            answer = copilot.chat(
                recipe_items,
                action_instruction,
                project_name=project["name"],
                project_description=project.get("description", ""),
                db_brief=str(db_ctx["summary"]),
                history=messages,
                model=selected_model or None,
            )
            chat_slot.markdown(
                _chat_html(
                    pending_messages,
                    pending_status="Computing verified nutrition, cost & clean-label metrics",
                ),
                unsafe_allow_html=True,
            )
            messages = pending_messages + [
                {
                    "role": "assistant",
                    "text": answer["reply"],
                    "engine": answer["engine"],
                    "thought": answer.get("thought", ""),
                    "thought_summary": answer.get("thought_summary", ""),
                },
            ]
            st.session_state[chat_key] = messages[-30:]
            if answer["items"]:
                st.session_state[recipe_key] = answer["items"]
                st.session_state.pop(f"explain_{project['project_id']}", None)
                st.session_state.pop(f"cl_explain_{project['project_id']}", None)
            st.rerun()
    ui.autoscroll()

with right:
    with st.container(border=True, key="panel_spec"):
        if not has_formulation:
            st.markdown(_skeleton_spec_html(), unsafe_allow_html=True)
        else:
            status_label = f"v{saved_meta['version']} (Saved)" if saved_meta else "Draft (Unsaved)"
            status_badge_class = "conf-verified" if saved_meta else "conf-estimated"

            top_info, top_actions = st.columns([1.1, 2.3], vertical_alignment="center")
            with top_info:
                st.markdown(
                    f'<div style="font-size: 0.72rem; color: var(--muted); letter-spacing: 0.08em; text-transform: uppercase;">FORMULATION SPEC</div>'
                    f'<span class="conf {status_badge_class}">{status_label}</span>',
                    unsafe_allow_html=True,
                )
            with top_actions:
                b1, b2, b3, b4 = st.columns([0.8, 1.1, 0.75, 1.05])
                with b1:
                    if st.button("Save", key="save_form_btn", type="primary", use_container_width=True):
                        ok, msg, form_id = formulations.save_project_formulation(
                            project_id=project["project_id"],
                            items=recipe_items,
                            user_id=user["user_id"],
                        )
                        if ok:
                            st.session_state[f"save_notice_{project['project_id']}"] = msg
                            st.rerun()
                        else:
                            st.error(msg)
                with b2:
                    st.download_button(
                        "Export Spec",
                        data=spec_sheet_md,
                        file_name=f"smartcrop_lab_spec_{project['project_id']}.md",
                        mime="text/markdown",
                        key="download_spec_btn",
                        use_container_width=True,
                    )
                with b3:
                    if st.button("Reset", key="reset_recipe_btn", use_container_width=True):
                        st.session_state[recipe_key] = []
                        st.session_state[chat_key] = list(OPENING_CHAT)
                        st.session_state.pop(f"explain_{project['project_id']}", None)
                        st.session_state.pop(f"cl_explain_{project['project_id']}", None)
                        st.session_state[f"save_notice_{project['project_id']}"] = "Cleared formulation back to empty skeleton."
                        st.rerun()
                with b4:
                    if st.button(
                        "AI draft",
                        key="ai_draft_btn",
                        icon=":material/auto_awesome:",
                        use_container_width=True,
                    ):
                        st.session_state.pop("ai_draft_result", None)
                        ai_draft_dialog(project["name"], project["project_id"])

            st.write("")

            # Clean label summary for KPI strip
            flagged = sum(1 for finding in findings if finding["status"] == "flagged")
            review = len(findings) - flagged
            if flagged:
                verdict_short, verdict_sub = f"{flagged} Flagged", "Needs replacement"
            elif review:
                verdict_short, verdict_sub = f"{review} Review", "Confirm source"
            else:
                verdict_short, verdict_sub = "Clean", "0 synthetic additives"

            # KPI Strip
            st.markdown(
                f'<div class="kpi-strip">'
                f'<div class="kpi-card">'
                f'<div class="kpi-label">Cost / kg</div>'
                f'<div class="kpi-value">₹{blend_cost:,.2f}</div>'
                f'<div class="kpi-note">{delta_text}</div>'
                f'</div>'
                f'<div class="kpi-card">'
                f'<div class="kpi-label">Protein</div>'
                f'<div class="kpi-value">{blend["protein_g"]:.1f}g</div>'
                f'<div class="kpi-note">per 100g blend</div>'
                f'</div>'
                f'<div class="kpi-card">'
                f'<div class="kpi-label">Energy</div>'
                f'<div class="kpi-value">{blend["energy_kcal"]:.0f}</div>'
                f'<div class="kpi-note">kcal / 100g</div>'
                f'</div>'
                f'<div class="kpi-card">'
                f'<div class="kpi-label">Clean Label</div>'
                f'<div class="kpi-value">{verdict_short}</div>'
                f'<div class="kpi-note">{verdict_sub}</div>'
                f'</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

            # Tabbed detail tables
            tab_recipe, tab_nutrition, tab_cost, tab_clean, tab_versions = st.tabs(
                [
                    ":material/science: Formulation",
                    ":material/bar_chart: Nutrition",
                    ":material/payments: Cost",
                    ":material/eco: Additive Check",
                    ":material/history: Versions",
                ]
            )

            with tab_recipe:
                st.markdown(_rows_html(recipe, blend_cost=blend_cost), unsafe_allow_html=True)
                st.markdown(
                    f'<div class="panel-note" style="margin-top: 0.6rem;">{len(recipe)} ingredients from the local crop database '
                    f"({catalog_size} seeded). Composition and prices are marked estimated until the lab "
                    "verifies them. The recipe updates live with every chat response.</div>",
                    unsafe_allow_html=True,
                )

            with tab_nutrition:
                st.markdown(_nutrition_html(blend), unsafe_allow_html=True)
                explain_key = f"explain_{project['project_id']}"
                if st.button(
                    "Explain this blend",
                    key="explain_blend_btn",
                    icon=":material/auto_awesome:",
                    width="stretch",
                ):
                    with st.spinner("Reading the blend…"):
                        try:
                            st.session_state[explain_key] = copilot.explain_blend(
                                recipe_items, model=selected_model or None
                            )
                        except gemini.GeminiError as exc:
                            st.warning(str(exc))
                if st.session_state.get(explain_key):
                    st.markdown(ui.ai_note(st.session_state[explain_key]), unsafe_allow_html=True)
                st.markdown(
                    f'<div class="panel-note" style="margin-top: 0.6rem;">Computed from the ingredient table. '
                    f"{quality['estimated']} of {len(recipe)} rows estimated"
                    + (f", {quality['unknown']} unknown" if quality["unknown"] else "")
                    + (f", {quality['verified']} verified" if quality["verified"] else "")
                    + ".</div>",
                    unsafe_allow_html=True,
                )

            with tab_cost:
                st.markdown(
                    f'<div class="cost-big">₹{blend_cost:,.2f}<span class="cost-unit">per kg</span></div>'
                    f'<span class="{delta_class}">{delta_text}</span>',
                    unsafe_allow_html=True,
                )
                st.markdown(
                    '<div class="cost-line" style="margin-top: 0.8rem;"><span>Reference base</span>'
                    f'<span>₹{baseline_cost:,.2f} / kg</span></div>'
                    f'<div class="cost-line"><span>Per {nutrition.SERVING_GRAMS} g serving</span>'
                    f'<span>₹{serving_cost:,.2f}</span></div>',
                    unsafe_allow_html=True,
                )
                st.markdown(
                    '<div class="panel-note" style="margin-top: 0.6rem;">Ingredient cost only, from mandi prices dated '
                    "2026-11-20; labour, packaging and losses are not included. The reference base is a "
                    "plain wheat-atta snack costed from the same table.</div>",
                    unsafe_allow_html=True,
                )

            with tab_clean:
                st.markdown(_clean_label_html(findings), unsafe_allow_html=True)
                cl_key = f"cl_explain_{project['project_id']}"
                if findings and st.button(
                    "What do these ingredients do?",
                    key="cl_explain_btn",
                    icon=":material/auto_awesome:",
                    width="stretch",
                ):
                    with st.spinner("Checking watchlist notes…"):
                        try:
                            st.session_state[cl_key] = copilot.explain_clean_label(
                                findings, model=selected_model or None
                            )
                        except gemini.GeminiError as exc:
                            st.warning(str(exc))
                if st.session_state.get(cl_key):
                    st.markdown(ui.ai_note(st.session_state[cl_key]), unsafe_allow_html=True)
                st.markdown(
                    f'<div class="panel-note" style="margin-top: 0.6rem;">Checked against a watchlist of '
                    f"{len(cleanlabel.watchlist())} synthetic terms and each ingredient's clean-label "
                    "flag. Natural crop replacements are recommended automatically.</div>",
                    unsafe_allow_html=True,
                )

            with tab_versions:
                if not versions:
                    st.markdown(
                        '<div class="panel-note">No saved versions yet. Press Save to create v1 — every '
                        "later save adds another version, and this tab compares any two of them.</div>",
                        unsafe_allow_html=True,
                    )
                else:
                    version_labels = [
                        f"v{version['version']} · {version['created_at'][:16]}" for version in versions
                    ]
                    pick_a, pick_b = st.columns(2)
                    label_a = pick_a.selectbox(
                        "Version A",
                        version_labels,
                        index=min(1, len(version_labels) - 1),
                        key=f"cmp_a_{project['project_id']}",
                    )
                    label_b = pick_b.selectbox(
                        "Version B",
                        version_labels,
                        index=0,
                        key=f"cmp_b_{project['project_id']}",
                    )
                    items_a = formulations.formulation_items(
                        versions[version_labels.index(label_a)]["formulation_id"]
                    )
                    items_b = formulations.formulation_items(
                        versions[version_labels.index(label_b)]["formulation_id"]
                    )
                    blend_a = nutrition.blend_nutrition(formulations.resolve(items_a))
                    blend_b = nutrition.blend_nutrition(formulations.resolve(items_b))
                    cost_a = nutrition.cost_per_kg(formulations.resolve(items_a))
                    cost_b = nutrition.cost_per_kg(formulations.resolve(items_b))

                    def _movement(before: float, after: float, label: str, decimals: int = 1) -> str:
                        diff = after - before
                        tone = "cost-delta up" if diff > 0 else "cost-delta"
                        return (
                            f'<div class="stat-row"><span class="stat-label">{ui.esc(label)}</span>'
                            f'<span class="stat-value">{before:,.{decimals}f} → {after:,.{decimals}f}'
                            f' <span class="{tone}" style="font-size: 0.66rem;">'
                            f"{diff:+,.{decimals}f}</span></span></div>"
                        )

                    st.markdown(
                        _movement(blend_a["protein_g"], blend_b["protein_g"], "Protein (g / 100 g)")
                        + _movement(
                            blend_a["energy_kcal"], blend_b["energy_kcal"], "Energy (kcal / 100 g)", 0
                        )
                        + _movement(cost_a, cost_b, "Cost (₹ / kg)", 2),
                        unsafe_allow_html=True,
                    )
                    st.markdown(
                        _compare_html(formulations.compare_items(items_a, items_b), label_a, label_b),
                        unsafe_allow_html=True,
                    )
                    if st.button(
                        f"Load {label_b} into the workbench",
                        key=f"load_cmp_{project['project_id']}",
                        width="stretch",
                    ):
                        st.session_state[recipe_key] = items_b
                        st.session_state[chat_key] = list(OPENING_CHAT)
                        st.session_state[f"save_notice_{project['project_id']}"] = (
                            f"Loaded {label_b} into the workbench. Save to keep it as a new version."
                        )
                        st.rerun()

