"""Audit log: everything the lab did, in one place, read-only.

The app already writes an event for every sign-in, account change, access grant,
project creation, saved formulation and data verification. This page just shows
that record honestly: who, when, what changed, and from what to what.
"""

from __future__ import annotations

import csv
import io

import streamlit as st

import auth
import ui
from storage import now

user = auth.require_admin()
events = auth.read_audit_log()
names = auth.user_names()

TABLE_LABELS = {
    "users": "People",
    "projects": "Project",
    "formulations": "Formulation",
    "ingredients": "Ingredient data",
    "project_access": "Project access",
}


def _area_label(table: str) -> str:
    return TABLE_LABELS.get(table, (table or "other").replace("_", " ").title())


@st.dialog("Audit entry", width="large")
def event_dialog(event: dict[str, str], actor_name: str) -> None:
    """One change in full, including the lab report that was attached to it."""
    st.markdown(f"**{ui.esc(event['note'] or 'Updated')}**")
    st.caption(
        f"{_area_label(event['table'])} · record {event['record_id'] or '—'} · {event['at']}"
    )

    left, right = st.columns(2)
    with left:
        st.markdown('<div class="panel-label">Who</div>', unsafe_allow_html=True)
        st.markdown(f"{ui.esc(actor_name)}")
        st.markdown(
            '<div class="panel-label" style="margin-top: 0.7rem;">Field</div>',
            unsafe_allow_html=True,
        )
        st.markdown(f"{ui.esc(event['field'] or '—')}")
    with right:
        st.markdown('<div class="panel-label">Change</div>', unsafe_allow_html=True)
        st.markdown(
            f"{ui.esc(event['old_value'] or '—')} → {ui.esc(event['new_value'] or '—')}"
        )
        st.markdown(
            '<div class="panel-label" style="margin-top: 0.7rem;">Event</div>',
            unsafe_allow_html=True,
        )
        st.markdown(f"<code>{ui.esc(event['event_id'])}</code>", unsafe_allow_html=True)

    st.markdown(
        '<div class="panel-label" style="margin-top: 0.9rem;">Lab report</div>',
        unsafe_allow_html=True,
    )
    if not event.get("lab_report"):
        st.caption("No lab report was attached to this change.")
        return

    report_path = auth.lab_report_path(event["lab_report"])
    if report_path is None:
        st.caption(f"The attached file is missing from disk: {event['lab_report']}")
        return

    size = report_path.stat().st_size
    st.caption(
        f"{report_path.name} · " + (f"{size / 1024:,.0f} KB" if size >= 1024 else f"{size:,} B")
    )
    st.download_button(
        "Download lab report",
        data=report_path.read_bytes(),
        file_name=report_path.name,
        key=f"audit_report_{event['event_id']}",
        width="stretch",
    )


today = now()[:10]
todays_events = sum(1 for event in events if event["at"][:10] == today)
verifications = sum(
    1 for event in events if event["table"] == "ingredients" and "verification" in event["note"].lower()
)

with st.container(key="audit_layout"):
    with st.container(key="audit_head"):
        top_l, top_r = st.columns([3.5, 1.2], vertical_alignment="center")
        with top_l:
            st.markdown(
                f'<div class="wb-eyebrow">{ui.esc(user["lab_id"])} · AUDIT LOG</div>',
                unsafe_allow_html=True,
            )
            st.title("Audit log")
            st.caption(
                "A running record of sign-ins, account changes, access grants, saved "
                "formulations and crop data edits. Open an entry to see the change in full and "
                "the lab report behind it. Read-only — nothing here can be edited or deleted "
                "from the app."
            )
        with top_r:
            st.page_link("pages/4_Lab_admin.py", label="← Back to Lab admin")

    stat_col1, stat_col2, stat_col3 = st.columns(3)
    with stat_col1:
        with st.container(
            border=True, key="stat_events", height=130, vertical_alignment="center", horizontal_alignment="left"
        ):
            st.markdown(
                '<div class="stat-card-inner">'
                '<div class="panel-label">Events recorded</div>'
                f'<div class="cost-big" style="font-size: 1.8rem !important; margin: 0.15rem 0;">{len(events)}</div>'
                '<div class="panel-note" style="margin-top: 0.2rem;">Since the lab was set up</div>'
                "</div>",
                unsafe_allow_html=True,
            )
    with stat_col2:
        with st.container(
            border=True, key="stat_today", height=130, vertical_alignment="center", horizontal_alignment="left"
        ):
            st.markdown(
                '<div class="stat-card-inner">'
                '<div class="panel-label">Today</div>'
                f'<div class="cost-big" style="font-size: 1.8rem !important; margin: 0.15rem 0;">{todays_events}</div>'
                f'<div class="panel-note" style="margin-top: 0.2rem;">Events on {today}</div>'
                "</div>",
                unsafe_allow_html=True,
            )
    with stat_col3:
        with st.container(
            border=True, key="stat_verifications", height=130, vertical_alignment="center", horizontal_alignment="left"
        ):
            st.markdown(
                '<div class="stat-card-inner">'
                '<div class="panel-label">Data verifications</div>'
                f'<div class="cost-big" style="font-size: 1.8rem !important; margin: 0.15rem 0;">{verifications}</div>'
                '<div class="panel-note" style="margin-top: 0.2rem;">Ingredient rows checked by a person</div>'
                "</div>",
                unsafe_allow_html=True,
            )

    actor_ids = sorted({event["actor_user_id"] for event in events})
    actor_options = ["Everyone"] + [names.get(actor_id, actor_id) for actor_id in actor_ids]
    actor_lookup = {names.get(actor_id, actor_id): actor_id for actor_id in actor_ids}

    table_options = ["All areas"] + sorted({_area_label(event["table"]) for event in events})

    filter_col1, filter_col2, filter_col3 = st.columns([1.6, 1.6, 2.6], vertical_alignment="bottom")
    actor_choice = filter_col1.selectbox("Person", actor_options, key="audit_actor")
    area_choice = filter_col2.selectbox("Area", table_options, key="audit_area")
    search = filter_col3.text_input(
        "Search", placeholder="e.g. P-001, signed in, soy", key="audit_search"
    )

    filtered: list[dict[str, str]] = []
    for event in events:
        if actor_choice != "Everyone" and event["actor_user_id"] != actor_lookup.get(actor_choice):
            continue
        if area_choice != "All areas" and _area_label(event["table"]) != area_choice:
            continue
        if search.strip():
            haystack = " ".join(
                [
                    names.get(event["actor_user_id"], ""),
                    event["table"],
                    event["record_id"],
                    event["field"],
                    event["old_value"],
                    event["new_value"],
                    event["note"],
                ]
            ).lower()
            if search.strip().lower() not in haystack:
                continue
        filtered.append(event)

    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=auth.AUDIT_FIELDS)
    writer.writeheader()
    for event in filtered:
        writer.writerow(event)

    with st.container(border=True, key="audit_table_card"):
        table_top_l, table_top_r = st.columns([3, 1.4], vertical_alignment="center")
        with table_top_l:
            st.markdown('<div class="panel-title">What happened</div>', unsafe_allow_html=True)
            st.caption(
                "Newest first. Open any entry to see who changed what, and the lab report if one "
                "was attached."
            )
        with table_top_r:
            st.download_button(
                "Download CSV",
                data=buffer.getvalue(),
                file_name="smartcrop_audit_log.csv",
                mime="text/csv",
                key="audit_download",
                width="stretch",
            )

        st.write("")

        header = st.columns([1.5, 2.2, 3.0, 1.6, 2.2, 0.9], vertical_alignment="center")
        for column, label in (
            (header[0], "When"),
            (header[1], "Who"),
            (header[2], "What happened"),
            (header[3], "Record"),
            (header[4], "Change"),
            (header[5], "Open"),
        ):
            column.markdown(f'<div class="roster-th">{label}</div>', unsafe_allow_html=True)

        st.markdown('<div class="roster-header-line"></div>', unsafe_allow_html=True)

        shown = filtered[:200]
        if not shown:
            st.markdown(
                '<div class="empty-state">No events match these filters.</div>',
                unsafe_allow_html=True,
            )

        for index, event in enumerate(shown):
            columns = st.columns([1.5, 2.2, 3.0, 1.6, 2.2, 0.9], vertical_alignment="center")
            event_day, _, event_time = event["at"].partition(" ")
            columns[0].markdown(
                f'<div class="roster-cell" style="height: auto; flex-direction: column; align-items: flex-start; padding: 0.2rem 0;">'
                f'<span style="font-weight: 600;">{ui.esc(event_time)}</span>'
                f'<span class="ing-local">{ui.esc(event_day)}</span>'
                "</div>",
                unsafe_allow_html=True,
            )
            columns[1].markdown(
                f'<div class="roster-cell roster-name">{ui.esc(names.get(event["actor_user_id"], event["actor_user_id"]))}</div>',
                unsafe_allow_html=True,
            )
            columns[2].markdown(
                f'<div class="roster-cell" style="height: auto; flex-direction: column; align-items: flex-start; padding: 0.2rem 0;">'
                f'<span>{ui.esc(event["note"] or "Updated")}</span>'
                f'<span class="ing-local">{ui.esc(_area_label(event["table"]))}</span>'
                "</div>",
                unsafe_allow_html=True,
            )
            record = event["record_id"] or "—"
            columns[3].markdown(
                f'<div class="roster-cell roster-email"><code>{ui.esc(record)}</code></div>',
                unsafe_allow_html=True,
            )

            if event["field"]:
                change = (
                    f'<span class="stat-label">{ui.esc(event["field"])}</span><br>'
                    f'<span style="font-size: 0.82rem;">{ui.esc(event["old_value"] or "—")} → '
                    f'{ui.esc(event["new_value"] or "—")}</span>'
                )
            else:
                change = f'<span style="font-size: 0.82rem;">{ui.esc(event["new_value"] or "—")}</span>'
            if event.get("lab_report"):
                change += ' <span class="conf conf-verified">report</span>'
            columns[4].markdown(
                f'<div class="roster-cell" style="height: auto; align-items: flex-start; padding: 0.2rem 0;">{change}</div>',
                unsafe_allow_html=True,
            )

            if columns[5].button(
                "Open", key=f"audit_open_{event['event_id']}", width="stretch"
            ):
                event_dialog(
                    event, names.get(event["actor_user_id"], event["actor_user_id"])
                )

            if index < len(shown) - 1:
                st.markdown('<div class="roster-row-line"></div>', unsafe_allow_html=True)

        if len(filtered) > len(shown):
            st.markdown(
                f'<div class="panel-note" style="margin-top: 0.7rem;">Showing the newest '
                f"{len(shown)} of {len(filtered)} matching events — narrow the filters to see older "
                "ones, or download the CSV.</div>",
                unsafe_allow_html=True,
            )

    st.markdown(
        '<div class="panel-note" style="margin-top: 0.9rem;">The log is plain CSV on this machine '
        "(<code>data/audit_log.csv</code>), written by the app itself. For the competition this is "
        "demo-grade record-keeping; a production lab would need append-only storage the app cannot "
        "rewrite.</div>",
        unsafe_allow_html=True,
    )
