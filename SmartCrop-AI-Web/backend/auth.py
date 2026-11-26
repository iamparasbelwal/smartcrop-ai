"""Local demo authentication and account storage for SmartCrop.AI Web."""

from __future__ import annotations

import hashlib
import hmac
import secrets
from pathlib import Path

from storage import APP_DIR, DATA_DIR, next_sequential_id, now, read_csv, write_csv

LABS_CSV = DATA_DIR / "labs.csv"
USERS_CSV = DATA_DIR / "users.csv"
AUDIT_CSV = DATA_DIR / "audit_log.csv"
LAB_REPORTS_DIR = DATA_DIR / "lab_reports"

LAB_ID = "LAB-001"
LAB_NAME = "SmartCrop Demo Lab"

ROLE_LABELS = {"lab_admin": "Lab admin", "lab_worker": "Lab worker"}

SEED_ACCOUNTS = [
    ("U-001", "Paras Belwal", "paras@smartcrop.ai", "lab_admin", "Admin@123"),
    ("U-002", "Shivam", "shivam@smartcrop.ai", "lab_worker", "Worker@123"),
    ("U-003", "Shreyshi Bijalwan", "shreyshi@smartcrop.ai", "lab_worker", "Worker@123"),
]

LAB_FIELDS = ["lab_id", "lab_name", "created_at"]
USER_FIELDS = [
    "user_id",
    "lab_id",
    "name",
    "email",
    "role",
    "password_hash",
    "active",
    "created_at",
    "last_login_at",
]
AUDIT_FIELDS = [
    "event_id",
    "at",
    "actor_user_id",
    "table",
    "record_id",
    "field",
    "old_value",
    "new_value",
    "note",
    "lab_report",
]

_SCRYPT = {"n": 16384, "r": 8, "p": 1, "dklen": 32}
MIN_PASSWORD_LENGTH = 8


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode("utf-8"), salt=salt, **_SCRYPT)
    return "scrypt${}${}${}${}${}".format(
        _SCRYPT["n"], _SCRYPT["r"], _SCRYPT["p"], salt.hex(), digest.hex()
    )


def verify_password(password: str, stored: str) -> bool:
    try:
        scheme, n, r, p, salt_hex, digest_hex = (stored or "").split("$")
        if scheme != "scrypt":
            return False
        digest = hashlib.scrypt(
            (password or "").encode("utf-8"),
            salt=bytes.fromhex(salt_hex),
            n=int(n),
            r=int(r),
            p=int(p),
            dklen=len(digest_hex) // 2,
        )
    except (ValueError, MemoryError):
        return False
    return hmac.compare_digest(digest.hex(), digest_hex)


def _dummy_verify(password: str) -> None:
    hashlib.scrypt((password or "").encode("utf-8"), salt=b"smartcrop-timing", **_SCRYPT)


def bootstrap() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not read_csv(LABS_CSV, LAB_FIELDS):
        write_csv(LABS_CSV, LAB_FIELDS, [{"lab_id": LAB_ID, "lab_name": LAB_NAME, "created_at": now()}])
    if not read_csv(USERS_CSV, USER_FIELDS):
        rows = [
            {
                "user_id": user_id,
                "lab_id": LAB_ID,
                "name": name,
                "email": email,
                "role": role,
                "password_hash": hash_password(password),
                "active": "yes",
                "created_at": now(),
                "last_login_at": "",
            }
            for user_id, name, email, role, password in SEED_ACCOUNTS
        ]
        write_csv(USERS_CSV, USER_FIELDS, rows)
    if not AUDIT_CSV.exists():
        write_csv(AUDIT_CSV, AUDIT_FIELDS, [])


def _public(user: dict[str, str]) -> dict[str, str]:
    keep = ("user_id", "lab_id", "name", "email", "role")
    return {key: user.get(key, "") for key in keep}


def get_user(user_id: str) -> dict[str, str] | None:
    row = next((u for u in read_csv(USERS_CSV, USER_FIELDS) if u["user_id"] == user_id), None)
    if row is None or row["active"].strip().lower() != "yes":
        return None
    return _public(row)


def list_users(lab_id: str) -> list[dict[str, str]]:
    users = [u for u in read_csv(USERS_CSV, USER_FIELDS) if u["lab_id"] == lab_id]
    users.sort(key=lambda u: (u["role"] != "lab_admin", u["name"].lower()))
    return [_public(u) | {"active": u["active"], "last_login_at": u["last_login_at"]} for u in users]


def _find_index(users: list[dict[str, str]], email: str) -> int | None:
    email = email.strip().lower()
    for index, user in enumerate(users):
        if user["email"].strip().lower() == email:
            return index
    return None


def create_worker(name: str, email: str, password: str, actor_id: str) -> tuple[bool, str]:
    name = (name or "").strip()
    email = (email or "").strip()
    password = password or ""

    if not name:
        return False, "Enter the worker's full name."
    if "@" not in email or "." not in email.split("@")[-1] or " " in email:
        return False, "Enter a valid email address, for example worker@lab.org."
    if len(password) < MIN_PASSWORD_LENGTH:
        return False, f"Use at least {MIN_PASSWORD_LENGTH} characters for the password."

    users = read_csv(USERS_CSV, USER_FIELDS)
    if _find_index(users, email) is not None:
        return False, "An account with this email already exists."

    actor = next((u for u in users if u["user_id"] == actor_id), None)
    lab_id = actor["lab_id"] if actor else LAB_ID

    new_user = {
        "user_id": next_sequential_id("U", users, "user_id"),
        "lab_id": lab_id,
        "name": name,
        "email": email,
        "role": "lab_worker",
        "password_hash": hash_password(password),
        "active": "yes",
        "created_at": now(),
        "last_login_at": "",
    }
    users.append(new_user)
    write_csv(USERS_CSV, USER_FIELDS, users)
    log_event(
        actor_id,
        table="users",
        record_id=new_user["user_id"],
        new_value=f"{new_user['name']} <{new_user['email']}> lab_worker",
        note="Created worker account",
    )
    return True, f"Created {new_user['name']} ({new_user['email']}). They can sign in now."


def set_active(user_id: str, active: bool, actor_id: str) -> tuple[bool, str]:
    if user_id == actor_id:
        return False, "You cannot deactivate your own account."
    users = read_csv(USERS_CSV, USER_FIELDS)
    target = next((u for u in users if u["user_id"] == user_id), None)
    if target is None:
        return False, "Account not found."
    old = target["active"]
    target["active"] = "yes" if active else "no"
    write_csv(USERS_CSV, USER_FIELDS, users)
    log_event(
        actor_id,
        table="users",
        record_id=user_id,
        field="active",
        old_value=old,
        new_value=target["active"],
        note="Reactivated account" if active else "Deactivated account",
    )
    return True, ("Reactivated" if active else "Deactivated") + f" {target['name']}."


def log_event(
    actor_id: str,
    *,
    table: str,
    record_id: str,
    field: str = "",
    old_value: str = "",
    new_value: str = "",
    note: str = "",
    lab_report: str = "",
) -> None:
    rows = read_csv(AUDIT_CSV, AUDIT_FIELDS)
    numbers = [
        int(row["event_id"].split("-")[-1])
        for row in rows
        if row["event_id"].split("-")[-1].isdigit()
    ]
    rows.append(
        {
            "event_id": "E-{:06d}".format(max(numbers, default=0) + 1),
            "at": now(),
            "actor_user_id": actor_id,
            "table": table,
            "record_id": record_id,
            "field": field,
            "old_value": old_value,
            "new_value": new_value,
            "note": note,
            "lab_report": lab_report,
        }
    )
    write_csv(AUDIT_CSV, AUDIT_FIELDS, rows)


def save_lab_report(data: bytes, filename: str, record_id: str) -> str:
    LAB_REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = "".join(
        char if (char.isalnum() or char in " ._-") else "_"
        for char in Path(filename or "lab_report").name
    ).strip() or "lab_report"
    stamp = now().replace("-", "").replace(":", "").replace(" ", "-")
    path = LAB_REPORTS_DIR / f"{stamp}-{record_id}-{safe_name}"
    path.write_bytes(data)
    return path.relative_to(APP_DIR).as_posix()


def lab_report_path(relative: str) -> Path | None:
    if not (relative or "").strip():
        return None
    path = (APP_DIR / relative).resolve()
    try:
        if not path.is_relative_to(LAB_REPORTS_DIR.resolve()):
            return None
    except ValueError:
        return None
    return path if path.is_file() else None


def read_audit_log() -> list[dict[str, str]]:
    rows = read_csv(AUDIT_CSV, AUDIT_FIELDS)
    rows.sort(key=lambda row: (row["at"], row["event_id"]), reverse=True)
    return rows


def user_names() -> dict[str, str]:
    return {row["user_id"]: row["name"] for row in read_csv(USERS_CSV, USER_FIELDS)}


def authenticate(email: str, password: str) -> tuple[bool, str, dict[str, str] | None]:
    email = (email or "").strip().lower()
    password = password or ""
    if not email or not password:
        return False, "Enter both email and password.", None

    users = read_csv(USERS_CSV, USER_FIELDS)
    index = _find_index(users, email)
    if index is None:
        _dummy_verify(password)
        return False, "Email or password is incorrect.", None

    user = users[index]
    if not verify_password(password, user["password_hash"]):
        return False, "Email or password is incorrect.", None
    if user["active"].strip().lower() != "yes":
        return False, "This account has been deactivated. Ask your lab admin.", None

    user["last_login_at"] = now()
    write_csv(USERS_CSV, USER_FIELDS, users)
    log_event(user["user_id"], table="users", record_id=user["user_id"], note="Signed in")
    return True, "", _public(user)


def user_is_active(user_id: str) -> bool:
    row = next((u for u in read_csv(USERS_CSV, USER_FIELDS) if u["user_id"] == user_id), None)
    return row is not None and row["active"].strip().lower() == "yes"
