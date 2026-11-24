"""Per-project access: who may open — and later certify — a given project.

Rule: lab admins see every project in their lab, a project's creator always sees it, and
everyone else needs an explicit grant recorded here. The same grant will cover certifying
results, because only someone who can open a project should sign off on it.

Demo-grade, like the rest of the local data: one CSV plus a check on every page run.
"""

from __future__ import annotations

import auth
from storage import DATA_DIR, now, read_csv, write_csv

ACCESS_CSV = DATA_DIR / "project_access.csv"
ACCESS_FIELDS = ["project_id", "user_id", "granted_by", "granted_at"]


def bootstrap() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not ACCESS_CSV.exists():
        write_csv(ACCESS_CSV, ACCESS_FIELDS, [])


def list_grants(project_id: str) -> list[dict[str, str]]:
    return [row for row in read_csv(ACCESS_CSV, ACCESS_FIELDS) if row["project_id"] == project_id]


def is_granted(project_id: str, user_id: str) -> bool:
    return any(row["user_id"] == user_id for row in list_grants(project_id))


def can_view(project: dict[str, str] | None, user: dict[str, str] | None) -> bool:
    """Admins and the project's creator always can; everyone else needs a grant."""
    if project is None or user is None:
        return False
    if project["lab_id"] != user["lab_id"]:
        return False
    if user["role"] == "lab_admin" or project["created_by"] == user["user_id"]:
        return True
    return is_granted(project["project_id"], user["user_id"])


def grant(project_id: str, user_id: str, actor_id: str, project_name: str = "") -> tuple[bool, str]:
    """Give one person access to one project. Returns (ok, message)."""
    rows = read_csv(ACCESS_CSV, ACCESS_FIELDS)
    if any(row["project_id"] == project_id and row["user_id"] == user_id for row in rows):
        return False, "That person already has access to this project."

    rows.append(
        {
            "project_id": project_id,
            "user_id": user_id,
            "granted_by": actor_id,
            "granted_at": now(),
        }
    )
    write_csv(ACCESS_CSV, ACCESS_FIELDS, rows)
    auth.log_event(
        actor_id,
        table="project_access",
        record_id=project_id,
        field="user_id",
        new_value=user_id,
        note=f"Granted project access · {project_name}" if project_name else "Granted project access",
    )
    return True, "Access granted."


def revoke(project_id: str, user_id: str, actor_id: str, project_name: str = "") -> tuple[bool, str]:
    """Take one person's access to one project away. Returns (ok, message)."""
    rows = read_csv(ACCESS_CSV, ACCESS_FIELDS)
    remaining = [
        row for row in rows if not (row["project_id"] == project_id and row["user_id"] == user_id)
    ]
    if len(remaining) == len(rows):
        return False, "That person does not have access to this project."

    write_csv(ACCESS_CSV, ACCESS_FIELDS, remaining)
    auth.log_event(
        actor_id,
        table="project_access",
        record_id=project_id,
        field="user_id",
        old_value=user_id,
        note=f"Revoked project access · {project_name}" if project_name else "Revoked project access",
    )
    return True, "Access revoked."
