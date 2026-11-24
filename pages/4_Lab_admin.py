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
        # ---------- MAIN WINDOW: WIDE TWO-COLUMN LAB ADMIN DASHBOARD ----------
        # Title header on the left
        st.markdown(
            f'<div class="wb-eyebrow">{ui.esc(user["lab_id"])} · ADMINISTRATION</div>'
            f'<h1 class="wb-title" style="font-family: \'Newsreader\', Georgia, serif; font-size: 2.35rem; font-weight: 500; color: var(--ink); margin: 0.2rem 0 0.45rem 0; letter-spacing: -0.02em; line-height: 1.2;">Lab admin</h1>'
            f'<div style="font-size: 0.95rem; color: var(--muted); max-width: 680px; margin-bottom: 1.5rem; line-height: 1.5;">{ui.esc(auth.LAB_NAME)} ({ui.esc(user["lab_id"])}) — manage workers, roles, and project permissions.</div>',
            unsafe_allow_html=True,
        )

        col_left, col_right = st.columns([1.08, 1.0], gap="large")

        # Left Column: Expanded "Add a worker" card below the title text
        with col_left:
            with st.container(border=True, key="admin_add"):
                st.subheader("Add a worker")
                st.caption(
                    "A worker can sign in, see this lab's projects, and edit formulations. Only admins manage accounts."
                )

                with st.form("add_worker_form", clear_on_submit=True):
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

        # Right Column: "People in this lab" card (top) + "Project access" card (bottom)
        with col_right:
            # Top card: People in this lab
            with st.container(border=True, key="admin_people_box"):
                top_h, top_b = st.columns([2, 1], vertical_alignment="center")
                with top_h:
                    st.subheader("People in this lab")
                with top_b:
                    st.markdown(
                        f'<span class="conf conf-verified" style="float: right;">{len(active_people)} active</span>',
                        unsafe_allow_html=True,
                    )

                st.caption("Active lab members with access to SmartCrop.AI tools:")

                # Show first 4 members preview
                for person in people[:4]:
                    role_label = auth.ROLE_LABELS.get(person["role"], person["role"])
                    is_active = person["active"] == "yes"
                    status_style = "conf-verified" if is_active else "conf-flagged"
                    status_txt = "Active" if is_active else "Deactivated"

                    p_col1, p_col2 = st.columns([3, 1.2], vertical_alignment="center")
                    with p_col1:
                        st.markdown(
                            f'<div style="font-size: 0.88rem; font-weight: 500;">{ui.esc(person["name"])} '
                            f'<span style="font-size: 0.72rem; color: #6f6a60;">({role_label})</span></div>'
                            f'<div style="font-size: 0.76rem; color: #6f6a60;">{ui.esc(person["email"])}</div>',
                            unsafe_allow_html=True,
                        )
                    with p_col2:
                        st.markdown(
                            f'<span class="conf {status_style}" style="font-size: 0.65rem;">{status_txt}</span>',
                            unsafe_allow_html=True,
                        )
                    st.markdown('<div style="height: 6px;"></div>', unsafe_allow_html=True)

                if len(people) > 4:
                    st.caption(f"+ {len(people) - 4} more member(s)")

                st.write("")
                st.page_link(
                    "pages/5_People.py",
                    label="View & Manage All People →",
                    icon=":material/group:",
                )

            # Bottom card: Project Access Permissions directly below "People in this lab"
            with st.container(border=True, key="admin_access_card"):
                acc_top_l, acc_top_r = st.columns([2.6, 1.4], vertical_alignment="center")
                with acc_top_l:
                    st.subheader("Project access")
                with acc_top_r:
                    st.markdown(
                        f'<span class="conf conf-verified" style="float: right;">{len(lab_projects)} projects</span>',
                        unsafe_allow_html=True,
                    )

                st.caption(
                    "Projects start visible only to creators and admins. Configure team permissions so workers can open projects and certify results."
                )

                st.write("")
                if st.button("Manage Project Access →", key="btn_open_access", type="primary", use_container_width=True):
                    st.query_params["view"] = "project_access"
                    st.session_state["admin_view"] = "project_access"
                    st.rerun()
