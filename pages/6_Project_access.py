"""Project access page: manage which lab members can open and edit each project."""

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

with st.container(key="access_layout"):
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
            st.page_link("pages/4_Lab_admin.py", label="← Back to Lab admin")

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
