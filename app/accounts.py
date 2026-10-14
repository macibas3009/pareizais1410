"""F0 · lietotāju konti un sesijas. Kopīgs HTML formām un JSON API (docs/openapi.yaml, CR-4)."""

from __future__ import annotations

import re
import sqlite3
from datetime import datetime, timedelta, timezone

from app import security

SESSION_COOKIE = "session"
SESSION_TTL = timedelta(hours=8)
PASSWORD_MIN, PASSWORD_MAX = 12, 128

# Visi latviešu burti; vārdus var atdalīt ar atstarpi, defisi vai apostrofu
FULL_NAME_RE = re.compile(r"^[^\W\d_]+(?:[ '\-][^\W\d_]+)*$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def normalize_email(email: str) -> str:
    return email.strip().lower()


def validate_registration(email: str, full_name: str, password: str) -> list[dict]:
    """Atgriež lauku kļūdas līguma formātā: [{"field": ..., "issue": ...}]."""
    details = []
    if not email:
        details.append({"field": "email", "issue": "REQUIRED"})
    elif not EMAIL_RE.fullmatch(email) or len(email) > 254:
        details.append({"field": "email", "issue": "INVALID_FORMAT"})
    if not full_name:
        details.append({"field": "fullName", "issue": "REQUIRED"})
    elif not FULL_NAME_RE.fullmatch(full_name) or len(full_name) > 100:
        details.append({"field": "fullName", "issue": "INVALID_FORMAT"})
    if not password:
        details.append({"field": "password", "issue": "REQUIRED"})
    elif len(password) < PASSWORD_MIN:
        details.append({"field": "password", "issue": "TOO_SHORT"})
    elif len(password) > PASSWORD_MAX:
        details.append({"field": "password", "issue": "TOO_LONG"})
    return details


def register(conn: sqlite3.Connection, email: str, full_name: str, password: str) -> int | None:
    """Izveido kontu bez lomas. Atgriež None, ja e-pasts jau ir reģistrēts."""
    password_hash = security.hash_password(password)
    if conn.execute("SELECT 1 FROM users WHERE email = ?", (email,)).fetchone():
        return None
    try:
        cur = conn.execute(
            "INSERT INTO users (email, full_name, password_hash, created_at) VALUES (?, ?, ?, ?)",
            (email, full_name, password_hash, datetime.now(timezone.utc).isoformat()),
        )
    except sqlite3.IntegrityError:  # vienlaicīga reģistrācija ar to pašu e-pastu
        return None
    conn.commit()
    return cur.lastrowid


def authenticate(conn: sqlite3.Connection, email: str, password: str) -> sqlite3.Row | None:
    row = conn.execute("SELECT * FROM users WHERE email = ?", (normalize_email(email),)).fetchone()
    # Ja konta nav, tik un tā rēķina jaucējvērtību, lai atbildes laiks neatklātu konta esamību
    stored = row["password_hash"] if row else security.DUMMY_HASH
    if not security.verify_password(password, stored) or row is None:
        return None
    return row


def create_session(conn: sqlite3.Connection, user_id: int) -> str:
    token = security.new_session_token()
    expires = datetime.now(timezone.utc) + SESSION_TTL
    conn.execute(
        "INSERT INTO sessions (token_hash, user_id, expires_at) VALUES (?, ?, ?)",
        (security.token_hash(token), user_id, expires.isoformat()),
    )
    conn.commit()
    return token


def end_session(conn: sqlite3.Connection, token: str | None) -> None:
    if token:
        conn.execute("DELETE FROM sessions WHERE token_hash = ?", (security.token_hash(token),))
        conn.commit()


def user_by_session(conn: sqlite3.Connection, token: str | None) -> sqlite3.Row | None:
    if not token:
        return None
    return conn.execute(
        "SELECT u.* FROM sessions s JOIN users u ON u.id = s.user_id "
        "WHERE s.token_hash = ? AND s.expires_at > ?",
        (security.token_hash(token), datetime.now(timezone.utc).isoformat()),
    ).fetchone()


def user_out(row: sqlite3.Row) -> dict:
    return {"id": row["id"], "email": row["email"], "fullName": row["full_name"]}
