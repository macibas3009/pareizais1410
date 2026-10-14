"""F5 · uzdevumi un atgādinājumi (tikai sistēmā, bez e-pasta)."""

from __future__ import annotations

import sqlite3
from datetime import date, datetime, timezone

from app import audit

DESCRIPTION_MAX = 300

FIELD_LABELS = {"description": "Apraksts", "assignee_id": "Izpildītājs", "due": "Izpildes datums",
                "link": "Saistīts ar", "organization_id": "Saistīts ar (organizācija)"}
MESSAGES = {
    ("description", "REQUIRED"): "Ievadiet, kas jādara.",
    ("description", "TOO_LONG"): f"Apraksts nedrīkst būt garāks par {DESCRIPTION_MAX} rakstzīmēm.",
    ("assignee_id", "REQUIRED"): "Izvēlieties izpildītāju.",
    ("due", "REQUIRED"): "Ievadiet izpildes datumu.",
    ("link", "REQUIRED"): "Uzdevumam jābūt saistītam ar organizāciju vai pieprasījumu.",
}

_SELECT = (
    "SELECT t.id, t.description, t.due, t.done_at, t.assignee_id, u.full_name AS assignee, "
    "c.full_name AS created_by_name, t.organization_id, t.request_id, "
    "COALESCE(o.name, ro.name) AS organization, COALESCE(o.id, ro.id) AS org_id, r.subject AS request "
    "FROM tasks t JOIN users u ON u.id = t.assignee_id JOIN users c ON c.id = t.created_by "
    "LEFT JOIN organizations o ON o.id = t.organization_id "
    "LEFT JOIN requests r ON r.id = t.request_id LEFT JOIN organizations ro ON ro.id = r.organization_id "
)


def due_today(conn: sqlite3.Connection, user: sqlite3.Row, today: date, assignee_id: int | None = None) -> list[sqlite3.Row]:
    """F5 #1: neizpildīti uzdevumi ar datumu ≤ šodiena, nokavētie augšā."""
    where, params = _scope(user, assignee_id)
    return conn.execute(
        _SELECT + f"WHERE t.done_at IS NULL AND t.due <= ? AND {where} ORDER BY t.due, t.id",
        (today.isoformat(), *params),
    ).fetchall()


def upcoming(conn: sqlite3.Connection, user: sqlite3.Row, today: date, assignee_id: int | None = None) -> list[sqlite3.Row]:
    where, params = _scope(user, assignee_id)
    return conn.execute(
        _SELECT + f"WHERE t.done_at IS NULL AND t.due > ? AND {where} ORDER BY t.due, t.id",
        (today.isoformat(), *params),
    ).fetchall()


def recently_done(conn: sqlite3.Connection, user: sqlite3.Row, assignee_id: int | None = None, limit: int = 10) -> list[sqlite3.Row]:
    where, params = _scope(user, assignee_id)
    return conn.execute(
        _SELECT + f"WHERE t.done_at IS NOT NULL AND {where} ORDER BY t.done_at DESC LIMIT ?", (*params, limit)
    ).fetchall()


def for_request(conn: sqlite3.Connection, request_id: int) -> list[sqlite3.Row]:
    return conn.execute(_SELECT + "WHERE t.request_id = ? ORDER BY t.done_at IS NOT NULL, t.due", (request_id,)).fetchall()


def _scope(user: sqlite3.Row, assignee_id: int | None) -> tuple[str, tuple]:
    """Darbinieks redz savus uzdevumus, vadītājs visus vai izvēlēta darbinieka (F5 #3)."""
    if user["role"] == "vaditajs":
        return ("t.assignee_id = ?", (assignee_id,)) if assignee_id else ("1 = 1", ())
    return "t.assignee_id = ?", (user["id"],)


def read_form(form) -> dict:
    def as_id(name: str) -> int | None:
        value = form.get(name, "")
        return int(value) if value.isdigit() else None

    return {
        "description": " ".join(form.get("description", "").split()),
        "assignee_id": as_id("assignee_id"),
        "due": form.get("due", "").strip(),
        "organization_id": as_id("organization_id"),
        "request_id": as_id("request_id"),
    }


def validate(conn: sqlite3.Connection, values: dict, staff_ids: set[int]) -> list[dict]:
    details = []
    if not values["description"]:
        details.append({"field": "description", "issue": "REQUIRED"})
    elif len(values["description"]) > DESCRIPTION_MAX:
        details.append({"field": "description", "issue": "TOO_LONG"})
    if values["assignee_id"] not in staff_ids:
        details.append({"field": "assignee_id", "issue": "REQUIRED"})
    try:
        date.fromisoformat(values["due"])
    except ValueError:
        details.append({"field": "due", "issue": "REQUIRED"})
    # Saistīts ar organizāciju VAI pieprasījumu; ja ar pieprasījumu, organizāciju nosaka pieprasījums
    if values["request_id"]:
        if not conn.execute("SELECT 1 FROM requests WHERE id = ?", (values["request_id"],)).fetchone():
            details.append({"field": "link", "issue": "REQUIRED"})
        values["organization_id"] = None
    elif not values["organization_id"] or not conn.execute(
        "SELECT 1 FROM organizations WHERE id = ?", (values["organization_id"],)
    ).fetchone():
        details.append({"field": "link", "issue": "REQUIRED"})
    return details


def create(conn: sqlite3.Connection, user: sqlite3.Row, values: dict) -> int:
    cur = conn.execute(
        "INSERT INTO tasks (description, assignee_id, created_by, due, organization_id, request_id) VALUES (?, ?, ?, ?, ?, ?)",
        (values["description"], values["assignee_id"], user["id"], values["due"], values["organization_id"], values["request_id"]),
    )
    conn.commit()
    audit.log(conn, user["id"], "create", "task", cur.lastrowid)
    return cur.lastrowid


def complete(conn: sqlite3.Connection, task_id: int, user: sqlite3.Row) -> bool:
    """F5 #2: izpilda izpildītājs; vadītājs var atzīmēt jebkuru."""
    row = conn.execute("SELECT assignee_id FROM tasks WHERE id = ? AND done_at IS NULL", (task_id,)).fetchone()
    if row is None or (user["role"] != "vaditajs" and row["assignee_id"] != user["id"]):
        return False
    conn.execute("UPDATE tasks SET done_at = ? WHERE id = ?", (datetime.now(timezone.utc).isoformat(timespec="seconds"), task_id))
    conn.commit()
    return True
