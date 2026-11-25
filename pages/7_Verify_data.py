"""Verify data: the lab admin's check on the numbers every calculation depends on.

Nothing in this app invents nutrition or cost figures — the Python maths reads
`data/ingredients.csv`. So the honesty of the demo rests on whether a person has
actually checked those rows. This page is where the admin corrects a wrong number,
says what it was checked against, attaches the lab report, and signs the change into
the audit log.
"""

from __future__ import annotations

import streamlit as st

import auth
import ingredients
import ui

user = auth.require_admin()
rows = ingredients.list_ingredients()
counts = ingredients.verified_counts()
categories = sorted({row["category"] for row in rows})


def _next_confidence(current: str, confirmed: bool) -> str:
    """Verified when ticked; back to estimated only if it had been verified before."""
    if confirmed:
        return "verified"
    return "estimated" if current == "verified" else current


def _changed_fields(ingredient: dict[str, str], values: dict[str, float]) -> list[str]:
    """Which numbers the admin actually typed differently from the file."""
    return [
        field
        for field in ingredients.EDIT_FIELDS
        if abs(values[field] - ingredients.number(ingredient, field)) >= 0.005
    ]


@st.dialog("Verify crop data", width="large")
def verify_dialog(ingredient: dict[str, str]) -> None:
    """Let the admin correct the row, name the source, and attach proof."""
    iid = ingredient["ingredient_id"]
    st.markdown(
        f"**{ui.esc(ingredient['name'])}** · {ui.esc(ingredient.get('local_name') or 'no local name')}"
    )
    st.caption(
        f"{ingredient['category']} · {ingredient['region']} · source {ingredient['source_id']} "
        f"· last changed {ingredient['updated_at'] or 'never'}"
    )

    st.markdown(
        '<div class="panel-label" style="margin-top: 0.7rem;">Values on file</div>',
        unsafe_allow_html=True,
    )
    st.caption(
        "Correct a number only when your source gives you a better one. Every field you "
        "change is written to the audit log with your name and the source."
    )

    values: dict[str, float] = {}
    left_col, right_col = st.columns(2)
    for index, field in enumerate(ingredients.EDIT_FIELDS):
        spec = ingredients.NUMERIC_FIELDS[field]
        column = left_col if index % 2 == 0 else right_col
        values[field] = column.number_input(
            str(spec["label"]),
            min_value=0.0,
            value=float(ingredients.number(ingredient, field)),
            step=float(spec["step"]),
            format=str(spec["format"]),
            key=f"vd_val_{iid}_{field}",
        )

    changed = _changed_fields(ingredient, values)
    changed_nutrition = [field for field in changed if field != ingredients.COST_FIELD]
    cost_changed = ingredients.COST_FIELD in changed
    if changed:
        st.caption(
            "Changing: "
            + ", ".join(
                f"{ingredients.NUMERIC_FIELDS[field]['label'].split(' (')[0]} "
                f"{ingredients.display_value(field, ingredients.number(ingredient, field))} → "
                f"{ingredients.display_value(field, values[field])}"
                for field in changed
            )
        )

    st.markdown(
        '<div class="panel-label" style="margin-top: 0.7rem;">Proof</div>',
        unsafe_allow_html=True,
    )
    nutrition_ok = st.checkbox(
        "Nutrition values confirmed against a source",
        value=ingredient["nutrition_confidence"] == "verified",
        key=f"vd_nut_{iid}",
    )
    cost_ok = st.checkbox(
        f"Cost confirmed (mandi price dated {ingredient['cost_date'] or 'unknown'})",
        value=ingredient["cost_confidence"] == "verified",
        key=f"vd_cost_{iid}",
    )
    reference = st.text_input(
        "What did you check it against?",
        placeholder="e.g. IFCT 2017 entry, supplier CoA number, invoice date",
        key=f"vd_ref_{iid}",
    )
    report = st.file_uploader(
        "Lab report for proof",
        type=["pdf", "png", "jpg", "jpeg"],
        key=f"vd_report_{iid}",
        help="PDF or photo of the report behind these numbers. It is stored with your "
        "audit entry, so anyone reviewing the change can open it later.",
    )

    will_verify = (
        nutrition_ok and ingredient["nutrition_confidence"] != "verified"
    ) or (cost_ok and ingredient["cost_confidence"] != "verified")

    if st.button("Save and log it", type="primary", width="stretch"):
        if not changed and not will_verify:
            st.error("Nothing to save — correct a value, or tick a check that is not yet verified.")
            return

        if changed_nutrition and not nutrition_ok:
            st.error(
                "You changed nutrition values — tick 'Nutrition values confirmed against a source' "
                "as well, so the row is not left half-checked."
            )
            return

        if cost_changed and not cost_ok:
            st.error("You changed the cost — tick the cost confirmation as well.")
            return

        if not reference.strip():
            st.error("Say what you checked it against — a document or source name.")
            return

        lab_report = ""
        if report is not None:
            lab_report = auth.save_lab_report(report.getvalue(), report.name, iid)

        ok, message = ingredients.save_verification(
            iid,
            values=values,
            nutrition_confidence=_next_confidence(
                ingredient["nutrition_confidence"], nutrition_ok
            ),
            cost_confidence=_next_confidence(ingredient["cost_confidence"], cost_ok),
            actor_id=user["user_id"],
            reference=reference,
            lab_report=lab_report,
        )
        if ok:
            for field in ingredients.EDIT_FIELDS:
                st.session_state.pop(f"vd_val_{iid}_{field}", None)
            for key in (f"vd_ref_{iid}", f"vd_report_{iid}"):
                st.session_state.pop(key, None)
            st.session_state["verify_notice"] = message
            st.rerun()
        else:
            st.error(message)


with st.container(key="verify_layout"):
    with st.container(key="verify_head"):
        top_l, top_r = st.columns([3.5, 1.2], vertical_alignment="center")
        with top_l:
            st.markdown(
                f'<div class="wb-eyebrow">{ui.esc(user["lab_id"])} · DATA INTEGRITY</div>',
                unsafe_allow_html=True,
            )
            st.title("Verify data")
            st.caption(
                "Every nutrition and cost figure in this app is read from the local crop table. "
                "Open a crop to correct a value, say what you checked it against, and attach the "
                "lab report — the workbench stops calling the value an estimate."
            )
        with top_r:
            st.page_link("pages/8_Audit_log.py", label="Audit log →")

    notice = st.session_state.pop("verify_notice", "")
    if notice:
        st.success(notice)

    stat_col1, stat_col2, stat_col3 = st.columns(3)
    with stat_col1:
        with st.container(
            border=True, key="stat_crops", height=130, vertical_alignment="center", horizontal_alignment="left"
        ):
            st.markdown(
                '<div class="stat-card-inner">'
                '<div class="panel-label">Crops in database</div>'
                f'<div class="cost-big" style="font-size: 1.8rem !important; margin: 0.15rem 0;">{counts["ingredients"]}</div>'
                '<div class="panel-note" style="margin-top: 0.2rem;">Seeded local ingredients</div>'
                "</div>",
                unsafe_allow_html=True,
            )
    with stat_col2:
        with st.container(
            border=True, key="stat_nutrition", height=130, vertical_alignment="center", horizontal_alignment="left"
        ):
            st.markdown(
                '<div class="stat-card-inner">'
                '<div class="panel-label">Nutrition verified</div>'
                f'<div class="cost-big" style="font-size: 1.8rem !important; margin: 0.15rem 0;">{counts["nutrition_verified"]}</div>'
                f'<div class="panel-note" style="margin-top: 0.2rem;">of {counts["ingredients"]} rows'
                + (f" · {counts['nutrition_unknown']} still unknown" if counts["nutrition_unknown"] else "")
                + "</div></div>",
                unsafe_allow_html=True,
            )
    with stat_col3:
        with st.container(
            border=True, key="stat_cost", height=130, vertical_alignment="center", horizontal_alignment="left"
        ):
            st.markdown(
                '<div class="stat-card-inner">'
                '<div class="panel-label">Cost verified</div>'
                f'<div class="cost-big" style="font-size: 1.8rem !important; margin: 0.15rem 0;">{counts["cost_verified"]}</div>'
                '<div class="panel-note" style="margin-top: 0.2rem;">Mandi prices, single-day survey</div>'
                "</div>",
                unsafe_allow_html=True,
            )

    filter_col1, filter_col2, filter_col3 = st.columns([1.4, 1.6, 2.4], vertical_alignment="bottom")
    category = filter_col1.selectbox(
        "Category", ["All categories"] + categories, key="verify_category"
    )
    status = filter_col2.selectbox(
        "Show", ["All rows", "Needs verification", "Fully verified"], key="verify_status"
    )
    search = filter_col3.text_input(
        "Search crop", placeholder="e.g. ragi, soy, guar", key="verify_search"
    )

    visible: list[dict[str, str]] = []
    for row in rows:
        if category != "All categories" and row["category"] != category:
            continue
        fully_verified = (
            row["nutrition_confidence"] == "verified" and row["cost_confidence"] == "verified"
        )
        if status == "Needs verification" and fully_verified:
            continue
        if status == "Fully verified" and not fully_verified:
            continue
        haystack = f"{row['name']} {row['local_name']} {row['category']} {row['region']}".lower()
        if search.strip() and search.strip().lower() not in haystack:
            continue
        visible.append(row)

    with st.container(border=True, key="verify_table_card"):
        table_top_l, table_top_r = st.columns([3, 1], vertical_alignment="center")
        with table_top_l:
            st.markdown('<div class="panel-title">Crop database</div>', unsafe_allow_html=True)
            st.caption(
                "Confidence tags come from the data itself. Open a crop to edit its values, "
                "attach the lab report, and record who changed what."
            )
        with table_top_r:
            st.markdown(
                f'<span class="conf conf-verified" style="float: right;">{len(visible)} shown</span>',
                unsafe_allow_html=True,
            )

        st.write("")

        header = st.columns([3.0, 1.4, 1.0, 1.0, 1.1, 1.2, 1.2, 1.0, 1.2], vertical_alignment="center")
        for column, label, align in (
            (header[0], "Crop", "left"),
            (header[1], "Category", "left"),
            (header[2], "Energy", "right"),
            (header[3], "Protein", "right"),
            (header[4], "₹ / kg", "right"),
            (header[5], "Nutrition", "center"),
            (header[6], "Cost", "center"),
            (header[7], "Source", "left"),
            (header[8], "Action", "center"),
        ):
            column.markdown(
                f'<div class="roster-th" style="text-align: {align};">{label}</div>',
                unsafe_allow_html=True,
            )

        st.markdown('<div class="roster-header-line"></div>', unsafe_allow_html=True)

        if not visible:
            st.markdown(
                '<div class="empty-state">No crops match these filters.</div>',
                unsafe_allow_html=True,
            )

        for index, row in enumerate(visible):
            columns = st.columns(
                [3.0, 1.4, 1.0, 1.0, 1.1, 1.2, 1.2, 1.0, 1.2], vertical_alignment="center"
            )
            local_name = row.get("local_name") or ""
            columns[0].markdown(
                f'<div class="roster-cell roster-name" style="height: auto; flex-direction: column; align-items: flex-start; padding: 0.2rem 0;">'
                f"<span>{ui.esc(row['name'])}</span>"
                + (f'<span class="ing-local">{ui.esc(local_name)}</span>' if local_name else "")
                + "</div>",
                unsafe_allow_html=True,
            )
            columns[1].markdown(
                f'<div class="roster-cell roster-role"><span class="cat-tag">{ui.esc(row["category"])}</span></div>',
                unsafe_allow_html=True,
            )
            columns[2].markdown(
                f'<div class="roster-cell num" style="justify-content: flex-end;">{ingredients.number(row, "energy_kcal"):,.0f}</div>',
                unsafe_allow_html=True,
            )
            columns[3].markdown(
                f'<div class="roster-cell num" style="justify-content: flex-end;">{ingredients.number(row, "protein_g"):,.1f}g</div>',
                unsafe_allow_html=True,
            )
            columns[4].markdown(
                f'<div class="roster-cell num" style="justify-content: flex-end;">₹{ingredients.number(row, "cost_per_kg"):,.0f}</div>',
                unsafe_allow_html=True,
            )

            nutrition_conf = row["nutrition_confidence"] or "unknown"
            cost_conf = row["cost_confidence"] or "unknown"
            columns[5].markdown(
                f'<div class="roster-cell" style="justify-content: center;">'
                f'<span class="conf conf-{ui.esc(nutrition_conf)}">{ui.esc(nutrition_conf)}</span></div>',
                unsafe_allow_html=True,
            )
            columns[6].markdown(
                f'<div class="roster-cell" style="justify-content: center;">'
                f'<span class="conf conf-{ui.esc(cost_conf)}">{ui.esc(cost_conf)}</span></div>',
                unsafe_allow_html=True,
            )
            columns[7].markdown(
                f'<div class="roster-cell roster-email"><code>{ui.esc(row["source_id"])}</code></div>',
                unsafe_allow_html=True,
            )

            label = "Review" if nutrition_conf == "verified" and cost_conf == "verified" else "Verify"
            if columns[8].button(label, key=f"verify_open_{row['ingredient_id']}", width="stretch"):
                verify_dialog(row)

            if index < len(visible) - 1:
                st.markdown('<div class="roster-row-line"></div>', unsafe_allow_html=True)

    st.markdown(
        '<div class="panel-note" style="margin-top: 0.9rem;">Marking a row verified is a claim about '
        "your own checking, not a lab measurement. The demo seed is deliberately estimated, and the "
        "workbench keeps saying so until someone records a source here."
        "</div>",
        unsafe_allow_html=True,
    )
