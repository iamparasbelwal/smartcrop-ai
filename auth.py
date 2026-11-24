"""Local demo authentication and account storage for SmartCrop.AI.

Demo-grade security, NOT production: accounts live in a local CSV file, passwords
are stored as salted scrypt hashes, and the signed-in user is kept in Streamlit's
session state. A real identity provider is a later milestone.

Roles: ``lab_admin`` and ``lab_worker``. Every user belongs to one ``lab_id``.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets
from pathlib import Path

import streamlit as st

from storage import DATA_DIR, next_sequential_id, now, read_csv, write_csv

APP_DIR = Path(__file__).resolve().parent
LABS_CSV = DATA_DIR / "labs.csv"
USERS_CSV = DATA_DIR / "users.csv"
AUDIT_CSV = DATA_DIR / "audit_log.csv"
SESSION_FILE = DATA_DIR / "session.json"

LAB_ID = "LAB-001"
LAB_NAME = "SmartCrop Demo Lab"

ROLE_LABELS = {"lab_admin": "Lab admin", "lab_worker": "Lab worker"}

# Seeded once, only when data/users.csv has no rows. Demo-only passwords.
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
]

_SCRYPT = {"n": 16384, "r": 8, "p": 1, "dklen": 32}
MIN_PASSWORD_LENGTH = 8


# --------------------------------------------------------------------------- #
# Passwords
# --------------------------------------------------------------------------- #
def hash_password(password: str) -> str:
    """Return ``scrypt$n$r$p$salt_hex$hash_hex`` for the given password."""
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
    """Spend roughly the same time as a real check so unknown emails are not obvious."""
    hashlib.scrypt((password or "").encode("utf-8"), salt=b"smartcrop-timing", **_SCRYPT)


# --------------------------------------------------------------------------- #
# Startup: create data files, seed the demo accounts
# --------------------------------------------------------------------------- #
def bootstrap() -> None:
    """Create the CSVs and the three seeded accounts if they do not exist yet."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if not read_csv(LABS_CSV, LAB_FIELDS):
        write_csv(
            LABS_CSV,
            LAB_FIELDS,
            [{"lab_id": LAB_ID, "lab_name": LAB_NAME, "created_at": now()}],
        )

    first_time_setup = not USERS_CSV.exists()

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

    # Pre-seed persistent session with demo admin ONLY on the very first setup if users.csv didn't exist
    if first_time_setup and not SESSION_FILE.exists():
        _save_persistent_session("U-001")


def _save_persistent_session(user_id: str) -> None:
    try:
        SESSION_FILE.write_text(json.dumps({"user_id": user_id, "saved_at": now()}), encoding="utf-8")
    except Exception:
        pass


def _clear_persistent_session() -> None:
    try:
        if SESSION_FILE.exists():
            SESSION_FILE.unlink()
    except Exception:
        pass


def _load_persistent_session() -> str | None:
    try:
        if SESSION_FILE.exists():
            data = json.loads(SESSION_FILE.read_text(encoding="utf-8"))
            return data.get("user_id")
    except Exception:
        pass
    return None


# --------------------------------------------------------------------------- #
# People
# --------------------------------------------------------------------------- #
def _public(user: dict[str, str]) -> dict[str, str]:
    keep = ("user_id", "lab_id", "name", "email", "role")
    return {key: user.get(key, "") for key in keep}


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


def _next_user_id(users: list[dict[str, str]]) -> str:
    return next_sequential_id("U", users, "user_id")


def create_worker(name: str, email: str, password: str, actor_id: str) -> tuple[bool, str]:
    """Create a lab_worker in the actor's lab. Returns (ok, message)."""
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
        "user_id": _next_user_id(users),
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


# --------------------------------------------------------------------------- #
# Audit log
# --------------------------------------------------------------------------- #
def log_event(
    actor_id: str,
    *,
    table: str,
    record_id: str,
    field: str = "",
    old_value: str = "",
    new_value: str = "",
    note: str = "",
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
        }
    )
    write_csv(AUDIT_CSV, AUDIT_FIELDS, rows)


# --------------------------------------------------------------------------- #
# Session
# --------------------------------------------------------------------------- #
def sign_in(email: str, password: str) -> tuple[bool, str]:
    """Check credentials and open a session. Returns (ok, error_message)."""
    email = (email or "").strip().lower()
    password = password or ""
    if not email or not password:
        return False, "Enter both email and password."

    users = read_csv(USERS_CSV, USER_FIELDS)
    index = _find_index(users, email)
    if index is None:
        _dummy_verify(password)
        return False, "Email or password is incorrect."

    user = users[index]
    if not verify_password(password, user["password_hash"]):
        return False, "Email or password is incorrect."
    if user["active"].strip().lower() != "yes":
        return False, "This account has been deactivated. Ask your lab admin."

    user["last_login_at"] = now()
    write_csv(USERS_CSV, USER_FIELDS, users)
    _save_persistent_session(user["user_id"])
    st.session_state["auth_user"] = _public(user)
    log_event(user["user_id"], table="users", record_id=user["user_id"], note="Signed in")
    return True, ""


def current_user() -> dict[str, str] | None:
    return st.session_state.get("auth_user")


def sign_out() -> None:
    user = current_user()
    if user:
        log_event(user["user_id"], table="users", record_id=user["user_id"], note="Signed out")
    _clear_persistent_session()
    st.session_state.pop("auth_user", None)
    st.session_state.pop("active_project_id", None)


def user_is_active(user_id: str) -> bool:
    """True only while the account still exists and is active."""
    row = next((u for u in read_csv(USERS_CSV, USER_FIELDS) if u["user_id"] == user_id), None)
    return row is not None and row["active"].strip().lower() == "yes"


def refresh_session_user() -> dict[str, str] | None:
    """Re-check the signed-in account on every run, so a deactivated worker is dropped."""
    session_user = st.session_state.get("auth_user")
    if session_user is None:
        persistent_uid = _load_persistent_session()
        if persistent_uid:
            row = next((u for u in read_csv(USERS_CSV, USER_FIELDS) if u["user_id"] == persistent_uid), None)
            if row and row["active"].strip().lower() == "yes":
                st.session_state["auth_user"] = _public(row)
                return st.session_state["auth_user"]
            else:
                _clear_persistent_session()
        return None

    row = next(
        (u for u in read_csv(USERS_CSV, USER_FIELDS) if u["user_id"] == session_user["user_id"]),
        None,
    )
    if row is None or row["active"].strip().lower() != "yes":
        _clear_persistent_session()
        st.session_state.pop("auth_user", None)
        st.session_state.pop("active_project_id", None)
        st.session_state["auth_notice"] = (
            "This account was deactivated by the lab admin. Ask your lab admin to reactivate it."
        )
        return None

    st.session_state["auth_user"] = _public(row)
    return st.session_state["auth_user"]


def force_sign_out(message: str) -> None:
    """Drop the session mid-use and explain why on the sign-in page."""
    user = current_user()
    if user:
        log_event(
            user["user_id"],
            table="users",
            record_id=user["user_id"],
            note="Session ended: account deactivated",
        )
    _clear_persistent_session()
    st.session_state.pop("auth_user", None)
    st.session_state.pop("active_project_id", None)
    st.session_state["auth_notice"] = message


def take_notice() -> str:
    """Return and clear a one-time message for the sign-in page."""
    return st.session_state.pop("auth_notice", "")


def require_login() -> dict[str, str]:
    user = current_user()
    if user is None:
        st.warning("Please sign in first.")
        st.stop()
    return user


def require_admin() -> dict[str, str]:
    user = require_login()
    if user["role"] != "lab_admin":
        st.error("Only a lab admin can open this page.")
        st.stop()
    return user
