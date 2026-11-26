"""People in this lab: dedicated team directory and member status page."""

from __future__ import annotations

import streamlit as st

import auth
import ui

user = auth.require_login()
ui.show_page_skeleton("people")
is_admin = user["role"] == "lab_admin"

with st.container(key="people_layout"):
    with st.container(key="people_head"):
        top_left, top_right = st.columns([3.5, 1.2], vertical_alignment="center")
        with top_left:
            st.markdown(f'<div class="wb-eyebrow">{ui.esc(user["lab_id"])} · TEAM DIRECTORY</div>', unsafe_allow_html=True)
            st.title("People in this lab")
            st.caption(f"{auth.LAB_NAME} — roster of researchers, lab workers, and administrators.")
        with top_right:
            if is_admin:
                st.page_link("pages/4_Lab_admin.py", label="← Back to Lab admin")

    people = auth.list_users(user["lab_id"])
    active_count = sum(1 for p in people if p["active"] == "yes")
    admin_count = sum(1 for p in people if p["role"] == "lab_admin")
    worker_count = sum(1 for p in people if p["role"] == "lab_worker")

    # Quick statistics cards
    stat_col1, stat_col2, stat_col3 = st.columns(3)
    with stat_col1:
        with st.container(border=True, key="stat_members", height=130, vertical_alignment="center", horizontal_alignment="left"):
            st.markdown(
                '<div class="stat-card-inner">'
                '<div class="panel-label">Total Members</div>'
                f'<div class="cost-big" style="font-size: 1.8rem !important; margin: 0.15rem 0;">{len(people)}</div>'
                f'<div class="panel-note" style="margin-top: 0.2rem;">{active_count} active accounts</div>'
                '</div>',
                unsafe_allow_html=True,
            )
    with stat_col2:
        with st.container(border=True, key="stat_admins", height=130, vertical_alignment="center", horizontal_alignment="left"):
            st.markdown(
                '<div class="stat-card-inner">'
                '<div class="panel-label">Lab Admins</div>'
                f'<div class="cost-big" style="font-size: 1.8rem !important; margin: 0.15rem 0;">{admin_count}</div>'
                '<div class="panel-note" style="margin-top: 0.2rem;">Full administration privileges</div>'
                '</div>',
                unsafe_allow_html=True,
            )
    with stat_col3:
        with st.container(border=True, key="stat_workers", height=130, vertical_alignment="center", horizontal_alignment="left"):
            st.markdown(
                '<div class="stat-card-inner">'
                '<div class="panel-label">Lab Workers</div>'
                f'<div class="cost-big" style="font-size: 1.8rem !important; margin: 0.15rem 0;">{worker_count}</div>'
                '<div class="panel-note" style="margin-top: 0.2rem;">Formulation and project access</div>'
                '</div>',
                unsafe_allow_html=True,
            )

    with st.container(border=True, key="people_table_card"):
        st.markdown('<div class="panel-title">Member Roster</div>', unsafe_allow_html=True)

        c_h = st.columns([2.6, 3.4, 1.8, 1.4, 2.0], vertical_alignment="center")
        c_h[0].markdown('<div class="roster-th">Name</div>', unsafe_allow_html=True)
        c_h[1].markdown('<div class="roster-th">Email</div>', unsafe_allow_html=True)
        c_h[2].markdown('<div class="roster-th">Role</div>', unsafe_allow_html=True)
        c_h[3].markdown('<div class="roster-th" style="text-align: center;">Status</div>', unsafe_allow_html=True)
        c_h[4].markdown(f'<div class="roster-th" style="text-align: center;">{"Actions" if is_admin else ""}</div>', unsafe_allow_html=True)

        st.markdown('<div class="roster-header-line"></div>', unsafe_allow_html=True)

        for i, person in enumerate(people):
            cols = st.columns([2.6, 3.4, 1.8, 1.4, 2.0], vertical_alignment="center")
            cols[0].markdown(f'<div class="roster-cell roster-name">{ui.esc(person["name"])}</div>', unsafe_allow_html=True)
            cols[1].markdown(f'<div class="roster-cell roster-email"><a href="mailto:{ui.esc(person["email"])}">{ui.esc(person["email"])}</a></div>', unsafe_allow_html=True)
            
            role_label = auth.ROLE_LABELS.get(person["role"], person["role"])
            cols[2].markdown(f'<div class="roster-cell roster-role">{ui.esc(role_label)}</div>', unsafe_allow_html=True)

            is_active = person["active"] == "yes"
            status_badge = "conf-verified" if is_active else "conf-flagged"
            status_text = "Active" if is_active else "Deactivated"
            cols[3].markdown(f'<div class="roster-cell" style="justify-content: center;"><span class="conf {status_badge}">{status_text}</span></div>', unsafe_allow_html=True)

            if is_admin:
                if person["user_id"] == user["user_id"]:
                    cols[4].markdown('<div class="roster-current-tag">You (Current)</div>', unsafe_allow_html=True)
                else:
                    btn_label = "Deactivate" if is_active else "Reactivate"
                    if cols[4].button(btn_label, key=f"people_toggle_{person['user_id']}", use_container_width=True):
                        ok, msg = auth.set_active(
                            person["user_id"], not is_active, actor_id=user["user_id"]
                        )
                        if ok:
                            st.rerun()
                        else:
                            st.error(msg)
            else:
                if person["user_id"] == user["user_id"]:
                    cols[4].markdown('<div class="roster-current-tag">You</div>', unsafe_allow_html=True)
                else:
                    cols[4].write("")

            if i < len(people) - 1:
                st.markdown('<div class="roster-row-line"></div>', unsafe_allow_html=True)
