"""Home: an assistant-style landing page for the lab's projects."""

from __future__ import annotations

from datetime import datetime

import streamlit as st

import auth
import formulations
import projects
import ui

user = auth.require_login()

hour = datetime.now().hour
greeting = "Good morning" if hour < 12 else ("Good afternoon" if hour < 17 else "Good evening")
first_name = user["name"].split()[0] if user["name"].split() else user["name"]

lab_projects = projects.list_visible_projects(user)
active_project = projects.active_project(user)
people = {person["user_id"]: person["name"] for person in auth.list_users(user["lab_id"])}
flash = st.session_state.pop("home_flash", "")

with st.container(key="home_layout"):
    with st.container(key="hero"):
        st.markdown(f'<div class="hero-eyebrow">{ui.esc(auth.LAB_NAME)}</div>', unsafe_allow_html=True)
        st.markdown(f'<h1 class="hero-title">{greeting}, {ui.esc(first_name)}</h1>', unsafe_allow_html=True)
        st.markdown(
            '<p class="hero-sub">What are we formulating today? Name a product and build a '
            "starting formulation from local crops.</p>",
            unsafe_allow_html=True,
        )

    if flash:
        st.success(flash)

    # Search Box on the left + Add New Project button on the right
    col_search, col_new = st.columns([3.5, 1.2], vertical_alignment="center")
    with col_search:
        search_query = st.text_input(
            "Search projects",
            placeholder="Search projects by name or description...",
            label_visibility="collapsed",
            key="home_search_input",
        ).strip().lower()

    with col_new:
        with st.popover("➕ New Project", use_container_width=True):
            st.markdown("**Create a new project**")
            with st.form("quick_new_project_form_home", clear_on_submit=True, border=False):
                new_name = st.text_input("Project name", placeholder="e.g. Lentil protein bar")
                new_desc = st.text_input("Short description (optional)", placeholder="e.g. High protein, gluten-free snack")
                create_btn = st.form_submit_button("Create & Open Workbench", type="primary", use_container_width=True)

            if create_btn:
                ok, msg, new_pid = projects.create_project(new_name, new_desc, user)
                if ok:
                    projects.set_active_project(new_pid)
                    st.switch_page("pages/2_Project.py")
                else:
                    st.error(msg)

    # Filter projects if query provided
    filtered_projects = [
        p for p in lab_projects
        if not search_query or search_query in p["name"].lower() or search_query in (p.get("description") or "").lower()
    ]

    st.markdown(
        '<div class="section-row" style="margin-top: 1.2rem; margin-bottom: 0.8rem;">'
        f'<div class="section-title">All Lab Projects ({len(filtered_projects)})</div>'
        '<div class="section-count">Click any project to open in Workbench</div>'
        "</div>",
        unsafe_allow_html=True,
    )

    if not filtered_projects:
        if search_query:
            st.markdown(
                f'<div class="empty-state">No projects matching “{ui.esc(search_query)}”. Try a different term or clear the search.</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div class="empty-state">No projects in this lab yet. Click “➕ New Project” above to start your first formulation.</div>',
                unsafe_allow_html=True,
            )
    else:
        for project in filtered_projects:
            is_active = (active_project or {}).get("project_id") == project["project_id"]
            active_badge = '<span class="card-badge" style="background: #edf1e4; color: #3f5230;">active</span>' if is_active else ""

            # Check saved formulation version
            saved_meta, _ = formulations.get_latest_project_formulation(project["project_id"])
            version_badge = (
                f'<span class="conf conf-verified" style="margin-left: 0.4rem;">v{saved_meta["version"]} Saved</span>'
                if saved_meta
                else '<span class="conf conf-estimated" style="margin-left: 0.4rem;">Draft</span>'
            )

            with st.container(border=True, key=f"pcard_{project['project_id']}", vertical_alignment="center"):
                left, right = st.columns([3.8, 1.4], vertical_alignment="center")
                with left:
                    creator = people.get(project["created_by"], project["created_by"])
                    desc_html = (
                        f'<div class="card-desc" style="margin: 0.25rem 0 0.35rem 0; font-size: 0.88rem; color: #4c4842; line-height: 1.4;">{ui.esc(project["description"])}</div>'
                        if project.get("description")
                        else '<div class="card-desc" style="margin: 0.25rem 0 0.35rem 0; font-size: 0.86rem; color: var(--muted); font-style: italic;">No description yet.</div>'
                    )
                    st.markdown(
                        f'<div class="project-info-block">'
                        f'<div class="card-title" style="font-size: 1.05rem; display: flex; align-items: center; gap: 0.45rem; flex-wrap: wrap; margin-bottom: 0.2rem;">'
                        f'<span>{ui.esc(project["name"])}</span>{active_badge}{version_badge}'
                        f'</div>'
                        f'{desc_html}'
                        f'<div class="card-meta" style="color: var(--muted); font-size: 0.74rem;">Created by {ui.esc(creator)} · {project["created_at"][:10]} · ID: <code>{ui.esc(project["project_id"])}</code></div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                with right:
                    btn_type = "primary" if is_active else "secondary"
                    btn_text = "Open Workbench →" if is_active else "Open Workbench"
                    if st.button(
                        btn_text,
                        key=f"home_open_wb_{project['project_id']}",
                        type=btn_type,
                        use_container_width=True,
                    ):
                        projects.set_active_project(project["project_id"])
                        st.switch_page("pages/2_Project.py")
