"""Lab projects: CSV storage and project listing for SmartCrop.AI Web."""

from __future__ import annotations

import access
import auth
import regions
from storage import DATA_DIR, next_sequential_id, now, read_csv, write_csv

PROJECTS_CSV = DATA_DIR / "projects.csv"
PROJECT_FIELDS = [
    "project_id",
    "lab_id",
    "name",
    "description",
    "target_region",
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


def _with_default_region(project: dict[str, str]) -> dict[str, str]:
    project["target_region"] = regions.normalize_region(project.get("target_region") or "Pan-India")
    return project


def list_projects(lab_id: str) -> list[dict[str, str]]:
    rows = [
        _with_default_region(project)
        for project in read_csv(PROJECTS_CSV, PROJECT_FIELDS)
        if project["lab_id"] == lab_id
    ]
    rows.sort(key=lambda project: (project["created_at"], project["project_id"]), reverse=True)
    return rows


def list_visible_projects(user: dict[str, str]) -> list[dict[str, str]]:
    return [project for project in list_projects(user["lab_id"]) if access.can_view(project, user)]


def get_project(project_id: str) -> dict[str, str] | None:
    proj = next(
        (project for project in read_csv(PROJECTS_CSV, PROJECT_FIELDS) if project["project_id"] == project_id),
        None,
    )
    return _with_default_region(proj) if proj else None


def create_project(
    name: str,
    description: str,
    user: dict[str, str],
    target_region: str = "Pan-India",
) -> tuple[bool, str, str]:
    name = (name or "").strip()
    description = (description or "").strip()
    norm_region = regions.normalize_region(target_region or "Pan-India")

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
        "target_region": norm_region,
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
        new_value=f"{name} ({norm_region})",
        note="Created project",
    )
    return True, f"Created project {name}.", project["project_id"]


def update_project_region(project_id: str, target_region: str, user: dict[str, str]) -> tuple[bool, str, str]:
    norm_region = regions.normalize_region(target_region or "Pan-India")
    rows = read_csv(PROJECTS_CSV, PROJECT_FIELDS)
    found = None
    for row in rows:
        if row["project_id"] == project_id:
            old_reg = row.get("target_region") or "Pan-India"
            row["target_region"] = norm_region
            row["updated_at"] = now()
            found = old_reg
            break
    if found is None:
        return False, "Project not found.", "Pan-India"
    write_csv(PROJECTS_CSV, PROJECT_FIELDS, rows)
    auth.log_event(
        user["user_id"],
        table="projects",
        record_id=project_id,
        field="target_region",
        old_value=found,
        new_value=norm_region,
        note="Updated project target region",
    )
    return True, f"Target region set to {norm_region}.", norm_region
