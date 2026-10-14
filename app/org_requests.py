"""F4 · pieprasījumi no organizācijām: statuss tikai uz priekšu, termiņš, kavējums tiek aprēķināts."""

from __future__ import annotations

import calendar
import sqlite3
from datetime import date

from app import audit, organizations

STATUSES = ("Jauns", "Darbā", "Atbildēts")
NEXT_STATUS = {"Jauns": "Darbā", "Darbā": "Atbildēts"}
NEXT_ACTION = {"Jauns": "Sākt darbu", "Darbā": "Atzīmēt kā atbildētu"}
SUBJECT_MAX = 200
DESCRIPTION_MAX = 2000

FIELD_LABELS = {"subject": "Temats", "description": "Apraksts", "received": "Saņemts", "due": "Termiņš"}
MESSAGES = {
    ("subject", "REQUIRED"): "Ievadiet pieprasījuma tematu.",
    ("subject", "TOO_LONG"): f"Temats nedrīkst būt garāks par {SUBJECT_MAX} rakstzīmēm.",
    ("description", "TOO_LONG"): f"Apraksts nedrīkst būt garāks par {DESCRIPTION_MAX} rakstzīmēm.",
    ("received", "REQUIRED"): "Ievadiet saņemšanas datumu.",
    ("received", "IN_FUTURE"): "Saņemšanas datums nevar būt nākotnē.",
    ("due", "REQUIRED"): "Ievadiet termiņu.",
    ("due", "BEFORE_RECEIVED"): "Termiņš nevar būt agrāks par saņemšanas datumu.",
}


def add_month(d: date) -> date:
    """Noklusētais termiņš: saņemšanas datums + 1 mēnesis (31.01. → 28./29.02.)."""
    year, month = (d.year + 1, 1) if d.month == 12 else (d.year, d.month + 1)
    return d.replace(year=year, month=month, day=min(d.day, calendar.monthrange(year, month)[1]))


def is_overdue(row: sqlite3.Row, today: date) -> bool:
    """Kavēts = termiņš pagājis un statuss nav "Atbildēts". Aprēķina, neglabā (F4 #2)."""
    return row["status"] != "Atbildēts" and row["due"] < today.isoformat()


def can_edit(user: sqlite3.Row, row: sqlite3.Row) -> bool:
    """Darbinieks pievieno un maina tikai savu organizāciju pieprasījumus, vadītājs visus (N3)."""
    return organizations.can_edit(user, row)


# --- Lasīšana ------------------------------------------------------------------


def get(conn: sqlite3.Connection, request_id: int) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT r.*, o.name AS organization, o.responsible_id, u.full_name AS responsible FROM requests r "
        "JOIN organizations o ON o.id = r.organization_id JOIN users u ON u.id = o.responsible_id WHERE r.id = ?",
        (request_id,),
    ).fetchone()


def list_filtered(conn: sqlite3.Connection, user: sqlite3.Row, today: date, status: str = "",
                  overdue: bool = False, mine: bool = False) -> list[sqlite3.Row]:
    where, params = ["1 = 1"], []
    if status in STATUSES:
        where.append("r.status = ?")
        params.append(status)
    elif status == "atverti":
        where.append("r.status != 'Atbildēts'")
    if overdue:
        where.append("r.status != 'Atbildēts' AND r.due < ?")
        params.append(today.isoformat())
    if mine:
        where.append("o.responsible_id = ?")
        params.append(user["id"])
    return conn.execute(
        "SELECT r.id, r.subject, r.status, r.received, r.due, o.id AS organization_id, o.name AS organization, "
        "o.responsible_id, u.full_name AS responsible FROM requests r "
        "JOIN organizations o ON o.id = r.organization_id JOIN users u ON u.id = o.responsible_id "
        f"WHERE {' AND '.join(where)} ORDER BY r.status = 'Atbildēts', r.due, r.id",
        params,
    ).fetchall()


# --- Forma un izmaiņas ---------------------------------------------------------


def read_form(form) -> dict:
    return {
        "subject": " ".join(form.get("subject", "").split()),
        "description": form.get("description", "").strip(),
        "received": form.get("received", "").strip(),
        "due": form.get("due", "").strip(),
    }


def validate(values: dict, today: date) -> list[dict]:
    details = []
    if not values["subject"]:
        details.append({"field": "subject", "issue": "REQUIRED"})
    elif len(values["subject"]) > SUBJECT_MAX:
        details.append({"field": "subject", "issue": "TOO_LONG"})
    if len(values["description"]) > DESCRIPTION_MAX:
        details.append({"field": "description", "issue": "TOO_LONG"})
    received = due = None
    try:
        received = date.fromisoformat(values["received"])
        if received > today:
            details.append({"field": "received", "issue": "IN_FUTURE"})
    except ValueError:
        details.append({"field": "received", "issue": "REQUIRED"})
    if not values["due"] and received:
        values["due"] = add_month(received).isoformat()  # tukšs termiņš → noklusējums
    try:
        due = date.fromisoformat(values["due"])
    except ValueError:
        details.append({"field": "due", "issue": "REQUIRED"})
    if received and due and due < received:
        details.append({"field": "due", "issue": "BEFORE_RECEIVED"})
    return details


def create(conn: sqlite3.Connection, user: sqlite3.Row, org_id: int, values: dict) -> int:
    cur = conn.execute(
        "INSERT INTO requests (organization_id, subject, description, received, due, status) VALUES (?, ?, ?, ?, ?, 'Jauns')",
        (org_id, values["subject"], values["description"] or None, values["received"], values["due"]),
    )
    conn.commit()
    audit.log(conn, user["id"], "create", "request", cur.lastrowid)
    return cur.lastrowid


def update(conn: sqlite3.Connection, user: sqlite3.Row, request_id: int, values: dict) -> None:
    conn.execute(
        "UPDATE requests SET subject = ?, description = ?, received = ?, due = ? WHERE id = ?",
        (values["subject"], values["description"] or None, values["received"], values["due"], request_id),
    )
    conn.commit()
    audit.log(conn, user["id"], "update", "request", request_id)


def advance(conn: sqlite3.Connection, user: sqlite3.Row, row: sqlite3.Row, target: str) -> bool:
    """Statuss tikai uz priekšu, vienu soli (F4 #1)."""
    if NEXT_STATUS.get(row["status"]) != target:
        return False
    conn.execute("UPDATE requests SET status = ? WHERE id = ?", (target, row["id"]))
    conn.commit()
    audit.log(conn, user["id"], "status", "request", row["id"])
    return True
