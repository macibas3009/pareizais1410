"""N2 · piekļuves žurnāls: kas skatīja vai mainīja ierakstu un kad. Žurnālā tikai ID, bez personas datiem."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

ACTION_LABELS = {
    "view": "Skatīja",
    "create": "Izveidoja",
    "update": "Laboja",
    "role_approve": "Apstiprināja lomu",
    "role_change": "Mainīja lomu",
    "role_reject": "Noraidīja kontu",
    "extend": "Pagarināja glabāšanas termiņu",
    "delete": "Dzēsa",
    "deletion_request": "Reģistrēja dzēšanas pieprasījumu",
    "deletion_reject": "Noraidīja dzēšanas pieprasījumu",
    "ai_generate": "Izveidoja MI kopsavilkumu",
    "ai_approve": "Apstiprināja MI kopsavilkumu",
    "status": "Mainīja statusu",
}
OBJECT_LABELS = {"organization": "Organizācija", "user": "Lietotājs", "contact": "Kontaktpersona", "interaction": "Mijiedarbība",
                 "request": "Pieprasījums", "task": "Uzdevums"}


def log(conn: sqlite3.Connection, user_id: int, action: str, object_type: str, object_id: int) -> None:
    conn.execute(
        "INSERT INTO access_log (user_id, action, object_type, object_id, at) VALUES (?, ?, ?, ?, ?)",
        (user_id, action, object_type, object_id, datetime.now(timezone.utc).isoformat(timespec="seconds")),
    )
    conn.commit()


def recent(conn: sqlite3.Connection, limit: int = 200) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT l.at, l.action, l.object_type, l.object_id, u.full_name AS user_name "
        "FROM access_log l JOIN users u ON u.id = l.user_id "
        "ORDER BY l.id DESC LIMIT ?",
        (limit,),
    ).fetchall()
