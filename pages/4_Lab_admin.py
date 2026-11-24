"""Lab admin page: manage who can sign in to this lab and project permissions."""

from __future__ import annotations

import streamlit as st

import access
import auth
import projects
import ui

user = auth.require_admin()
people = auth.list_users(user["lab_id"])
active_people = [person for person in people if person["active"] == "yes"]
lab_projects = projects.list_projects(user["lab_id"])

is_access_view = (
    st.query_params.get("view") == "project_access"
    or st.session_state.get("admin_view") == "project_access"
)

with st.container(key="admin_layout"):
    if is_access_view:
        # ---------- NEXT WINDOW: DEDICATED PROJECT ACCESS VIEW ----------
        with st.container(key="access_head"):
            top_l, top_r = st.columns([3.5, 1.2], vertical_alignment="center")
            with top_l:
                st.markdown(
                    f'<div class="wb-eyebrow">{ui.esc(user["lab_id"])} · PROJECT ACCESS</div>',
                    unsafe_allow_html=True,
                )
                st.title("Project access")
                st.caption(
                    "A project starts visible only to its creator and the lab admins. Grant access here so "
                    "someone else can open it — the same grant will let them certify results."
                )
            with top_r:
                if st.button("← Back to Lab admin", key="back_to_admin"):
                    st.query_params.pop("view", None)
                    st.session_state.pop("admin_view", None)
                    st.rerun()

        st.write("")

        if not lab_projects:
            st.markdown(
                '<div class="empty-state">No projects in this lab yet. Create one on Home first.</div>',
                unsafe_allow_html=True,
            )
        else:
            for project in lab_projects:
                granted = {row["user_id"] for row in access.list_grants(project["project_id"])}
                visible = sum(1 for person in active_people if access.can_view(project, person))

                with st.expander(
                    f"{project['name']} — {visible} of {len(active_people)} people can open it",
                    expanded=visible <= 1,
                ):
                    for person in active_people:
                        columns = st.columns([3, 3.4, 2.2, 2], vertical_alignment="center")
                        columns[0].write(person["name"])
                        columns[1].caption(person["email"])

                        if person["user_id"] == project["created_by"]:
                            columns[2].write("Creator")
                            columns[3].caption("Always")
                            continue
                        if person["role"] == "lab_admin":
                            columns[2].write(auth.ROLE_LABELS["lab_admin"])
                            columns[3].caption("Always")
                            continue

                        has_access = person["user_id"] in granted
                        columns[2].write("Can open" if has_access else "No access")
                        if columns[3].button(
                            "Revoke" if has_access else "Grant",
                            key=f"access_{project['project_id']}_{person['user_id']}",
                            width="stretch",
                        ):
                            if has_access:
                                ok, message = access.revoke(
                                    project["project_id"],
                                    person["user_id"],
                                    actor_id=user["user_id"],
                                    project_name=project["name"],
                                )
                            else:
                                ok, message = access.grant(
                                    project["project_id"],
                                    person["user_id"],
                                    actor_id=user["user_id"],
                                    project_name=project["name"],
                                )
                            if ok:
                                st.rerun()
                            else:
                                st.error(message)

    else:
        # ---------- MAIN WINDOW: LAB ADMIN DASHBOARD ----------
        # Title header row: Title on left, action buttons on right
        head_col_left, head_col_right = st.columns([2.3, 1.7], vertical_alignment="center")
        with head_col_left:
            st.markdown(f'<div class="wb-eyebrow">{ui.esc(user["lab_id"])} · ADMINISTRATION</div>', unsafe_allow_html=True)
            st.title("Lab admin")
            st.caption(f"{auth.LAB_NAME} ({ui.esc(user['lab_id'])}) — manage workers, roles, and project permissions.")

        with head_col_right:
            btn_col1, btn_col2 = st.columns([1, 1.3], vertical_alignment="center")
            with btn_col1:
                with st.popover("Add worker", icon=":material/person_add:", use_container_width=True):
                    st.markdown("**Add a worker**")
                    st.caption(
                        "A worker can sign in, see this lab's projects, and edit formulations. Only admins manage accounts."
                    )
                    with st.form("add_worker_form", clear_on_submit=True, border=False):
                        name = st.text_input("Full name", placeholder="e.g. Aditi Sharma")
                        email = st.text_input("Email", placeholder="worker@lab.org")
                        password = st.text_input("Temporary password", type="password")
                        st.caption(
                            f"At least {auth.MIN_PASSWORD_LENGTH} characters. Share it with the worker privately."
                        )
                        create = st.form_submit_button("Create worker account", type="primary", use_container_width=True)

                    if create:
                        ok, message = auth.create_worker(name, email, password, actor_id=user["user_id"])
                        if ok:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)

            with btn_col2:
                if st.button("Manage project access →", key="btn_top_access", type="primary", use_container_width=True):
                    st.query_params["view"] = "project_access"
                    st.session_state["admin_view"] = "project_access"
                    st.rerun()

        # Full-window People in this lab table
        with st.container(border=True, key="admin_people_table"):
            table_top_l, table_top_r = st.columns([3, 1], vertical_alignment="center")
            with table_top_l:
                st.markdown(
                    '<div class="panel-title">People in this lab</div>',
                    unsafe_allow_html=True,
                )
                st.caption("Active lab members with access to SmartCrop.AI tools:")
            with table_top_r:
                st.markdown(
                    f'<span class="conf conf-verified" style="float: right;">{len(active_people)} active</span>',
                    unsafe_allow_html=True,
                )

            st.write("")

            c_h = st.columns([2.6, 3.4, 1.8, 1.4, 2.0], vertical_alignment="center")
            c_h[0].markdown('<div class="roster-th">Name</div>', unsafe_allow_html=True)
            c_h[1].markdown('<div class="roster-th">Email</div>', unsafe_allow_html=True)
            c_h[2].markdown('<div class="roster-th">Role</div>', unsafe_allow_html=True)
            c_h[3].markdown('<div class="roster-th" style="text-align: center;">Status</div>', unsafe_allow_html=True)
            c_h[4].markdown('<div class="roster-th" style="text-align: center;">Actions</div>', unsafe_allow_html=True)

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

                if person["user_id"] == user["user_id"]:
                    cols[4].markdown('<div class="roster-current-tag">You (Current)</div>', unsafe_allow_html=True)
                else:
                    btn_label = "Deactivate" if is_active else "Reactivate"
                    if cols[4].button(btn_label, key=f"admin_toggle_{person['user_id']}", use_container_width=True):
                        ok, msg = auth.set_active(
                            person["user_id"], not is_active, actor_id=user["user_id"]
                        )
                        if ok:
                            st.rerun()
                        else:
                            st.error(msg)

                if i < len(people) - 1:
                    st.markdown('<div class="roster-row-line"></div>', unsafe_allow_html=True)
