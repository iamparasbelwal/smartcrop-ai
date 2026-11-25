"""Lab projects: CSV storage, creation, and which project is currently selected."""

from __future__ import annotations

import streamlit as st

import auth
import access
from storage import DATA_DIR, next_sequential_id, now, read_csv, write_csv

PROJECTS_CSV = DATA_DIR / "projects.csv"
PROJECT_FIELDS = [
    "project_id",
    "lab_id",
    "name",
    "description",
    "created_by",
    "created_at",
    "updated_at",
]
MAX_NAME_LENGTH = 120


def bootstrap() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    access.bootstrap()
    if not PROJECTS_CSV.exists():
        write_csv(PROJECTS_CSV, PROJECT_FIELDS, [])


def list_projects(lab_id: str) -> list[dict[str, str]]:
    """Every project of one lab, newest first. Not filtered by access."""
    rows = [project for project in read_csv(PROJECTS_CSV, PROJECT_FIELDS) if project["lab_id"] == lab_id]
    rows.sort(key=lambda project: (project["created_at"], project["project_id"]), reverse=True)
    return rows


def list_visible_projects(user: dict[str, str]) -> list[dict[str, str]]:
    """The lab's projects this user may open, newest first."""
    return [project for project in list_projects(user["lab_id"]) if access.can_view(project, user)]


def get_project(project_id: str) -> dict[str, str] | None:
    return next(
        (project for project in read_csv(PROJECTS_CSV, PROJECT_FIELDS) if project["project_id"] == project_id),
        None,
    )


def create_project(name: str, description: str, user: dict[str, str]) -> tuple[bool, str, str]:
    """Create a project in the user's lab. Returns (ok, message, project_id)."""
    name = (name or "").strip()
    description = (description or "").strip()

    if not name:
        return False, "Enter an end goal for the project.", ""
    if len(name) > MAX_NAME_LENGTH:
        return False, f"Keep the end goal under {MAX_NAME_LENGTH} characters.", ""

    rows = read_csv(PROJECTS_CSV, PROJECT_FIELDS)
    same_lab = [project for project in rows if project["lab_id"] == user["lab_id"]]
    if any(project["name"].strip().lower() == name.lower() for project in same_lab):
        return False, "This lab already has a project with that name.", ""

    project = {
        "project_id": next_sequential_id("P", rows, "project_id"),
        "lab_id": user["lab_id"],
        "name": name,
        "description": description,
        "created_by": user["user_id"],
        "created_at": now(),
        "updated_at": now(),
    }
    rows.append(project)
    write_csv(PROJECTS_CSV, PROJECT_FIELDS, rows)
    auth.log_event(
        user["user_id"],
        table="projects",
        record_id=project["project_id"],
        new_value=name,
        note="Created project",
    )
    return True, f"Created project {name}.", project["project_id"]


def set_active_project(project_id: str) -> None:
    st.session_state["active_project_id"] = project_id


def active_project(user: dict[str, str]) -> dict[str, str] | None:
    """The project selected in the sidebar, or None if unset/foreign/deleted/no access."""
    project_id = st.session_state.get("active_project_id")
    if not project_id:
        return None
    project = get_project(project_id)
    if project is None or project["lab_id"] != user["lab_id"]:
        st.session_state.pop("active_project_id", None)
        return None
    # A project the user may no longer open stays selected so the workbench can explain
    # why it is closed, rather than pretending nothing was chosen.
    if not access.can_view(project, user):
        return None
    return project


def denied_active_project(user: dict[str, str]) -> dict[str, str] | None:
    """The selected project when it exists in the lab but this user may not open it.

    Used only to explain the situation on the workbench, after the access check above
    has already cleared the selection.
    """
    project_id = st.session_state.get("active_project_id")
    if not project_id:
        return None
    project = get_project(project_id)
    if project is None or project["lab_id"] != user["lab_id"]:
        return None
    return None if access.can_view(project, user) else project
