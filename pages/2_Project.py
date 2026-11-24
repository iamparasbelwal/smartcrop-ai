"""Project workbench: formulation and what-if on the left, nutrition and cost on the right.

M3 shell only: the layout, the panels and every button are in place, but the rows are
placeholder data and the buttons do not change anything yet. Nothing here is saved.
"""

import streamlit as st

import auth
import cleanlabel
import formulations
import ingredients
import nutrition
import projects
import ui
import whatif

user = auth.require_login()
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
        "text": "Tell me what to change — more protein, lower cost, less sugar — and I'll rebalance "
        "the recipe and recompute the panels.",
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


def _chat_html(messages: list[dict]) -> str:
    rows = []
    for message in messages:
        role = "me" if message["role"] == "user" else "ai"
        text = ui.esc(message["text"]).replace("\n", "<br>")
        rows.append(f'<div class="chat-row {role}"><div class="chat-bubble">{text}</div></div>')
    return f'<div class="chat-log">{"".join(rows)}</div>'


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
if recipe_key not in st.session_state:
    st.session_state[recipe_key] = saved_items

recipe_items = st.session_state.get(recipe_key) or saved_items
messages = st.session_state.get(chat_key) or list(OPENING_CHAT)
recipe = formulations.resolve(recipe_items)
catalog_size = len(ingredients.list_ingredients())
blend = nutrition.blend_nutrition(recipe)
blend_cost = nutrition.cost_per_kg(recipe)
baseline_cost = nutrition.cost_per_kg(formulations.reference_base())
serving_cost = nutrition.cost_per_serving(recipe)
quality = nutrition.confidence_counts(recipe)
findings = cleanlabel.check(recipe)

# Build the lab spec sheet markdown for export
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

with left:
    with st.container(border=True, key="panel_chat"):
        st.markdown(
            '<div class="chat-header">'
            '<div class="panel-label">SMARTCROP CO-PILOT</div>'
            '<div class="panel-title" style="margin-bottom: 0;">Chat Assistant</div>'
            "</div>",
            unsafe_allow_html=True,
        )
        st.markdown(_chat_html(messages), unsafe_allow_html=True)

        st.markdown('<div class="chat-chips-label">Quick Prompts</div>', unsafe_allow_html=True)
        prompt_cols = st.columns(4)
        prompts = [
            ("⚡ More protein", "more protein"),
            ("💰 Lower cost", "lower cost"),
            ("🌾 More millet", "more millet"),
            ("🍯 Less sugar", "less sweet"),
        ]
        clicked_prompt = None
        for pcol, (plabel, pcmd) in zip(prompt_cols, prompts):
            if pcol.button(plabel, key=f"qp_{pcmd}", use_container_width=True):
                clicked_prompt = pcmd

        with st.form("workbench_chat_form", clear_on_submit=True, border=False):
            input_column, send_column = st.columns([4.2, 1.2], vertical_alignment="center")
            with input_column:
                instruction = st.text_input(
                    "Instruction",
                    key="workbench_chat_input",
                    placeholder="e.g. More protein, lower cost, less sugar, swap soy for chickpea...",
                    label_visibility="collapsed",
                )
            with send_column:
                sent = st.form_submit_button("Send ↵", type="primary", use_container_width=True)

        action_instruction = clicked_prompt or (instruction.strip() if sent else None)
        if action_instruction:
            new_items, reply, changed = whatif.apply(recipe_items, action_instruction)
            messages = messages + [
                {"role": "user", "text": action_instruction},
                {"role": "assistant", "text": reply},
            ]
            st.session_state[chat_key] = messages[-30:]
            if changed:
                st.session_state[recipe_key] = new_items
            st.rerun()

with right:
    with st.container(border=True, key="panel_spec"):
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
            b1, b2, b3 = st.columns([1.0, 1.3, 0.9])
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
                    st.session_state[recipe_key] = formulations.starter_items()
                    st.session_state[chat_key] = list(OPENING_CHAT)
                    st.session_state[f"save_notice_{project['project_id']}"] = "Reset to default starter recipe."
                    st.rerun()

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
        tab_recipe, tab_nutrition, tab_cost, tab_clean = st.tabs(
            ["🥣 Formulation", "📊 Nutrition", "💰 Cost", "🌿 Additive Check"]
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
            st.markdown(
                f'<div class="panel-note" style="margin-top: 0.6rem;">Checked against a watchlist of '
                f"{len(cleanlabel.watchlist())} synthetic terms and each ingredient's clean-label "
                "flag. Natural crop replacements are recommended automatically.</div>",
                unsafe_allow_html=True,
            )

