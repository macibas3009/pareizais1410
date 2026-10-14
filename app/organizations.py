"""F1 · organizācijas: saraksts, kartīte, izveide un labošana."""

from __future__ import annotations

import re
import sqlite3

KINDS = ("Uzņēmums", "NVO", "Pašvaldība")
REG_NO_RE = re.compile(r"^\d{11}$")  # pieņēmums: 11 cipari (prasību saraksts, 10. nodaļa, #1)
NAME_MIN, NAME_MAX = 2, 200

FIELD_LABELS = {
    "name": "Nosaukums",
    "reg_no": "Reģistrācijas nr.",
    "kind": "Veids",
    "responsible_id": "Atbildīgais darbinieks",
}
MESSAGES = {
    ("name", "REQUIRED"): "Ievadiet organizācijas nosaukumu.",
    ("name", "INVALID_LENGTH"): f"Nosaukumam jābūt {NAME_MIN}–{NAME_MAX} rakstzīmes garam.",
    ("reg_no", "REQUIRED"): "Ievadiet reģistrācijas numuru.",
    ("reg_no", "INVALID_FORMAT"): "Reģistrācijas numuram jābūt 11 cipariem, piemēram, 40003000001.",
    ("reg_no", "TAKEN"): "Organizācija ar šo reģ. nr. jau ir reģistrēta.",
    ("kind", "REQUIRED"): "Izvēlieties organizācijas veidu.",
    ("responsible_id", "REQUIRED"): "Izvēlieties atbildīgo darbinieku.",
}


def can_edit(user: sqlite3.Row, org: sqlite3.Row) -> bool:
    """Darbinieks labo tikai savas organizācijas, vadītājs visas (N3)."""
    return user["role"] == "vaditajs" or (user["role"] == "darbinieks" and org["responsible_id"] == user["id"])


def list_all(conn: sqlite3.Connection, kind: str | None = None, responsible_id: int | None = None) -> list[sqlite3.Row]:
    where, params = ["1 = 1"], []
    if kind in KINDS:
        where.append("o.kind = ?")
        params.append(kind)
    if responsible_id:
        where.append("o.responsible_id = ?")
        params.append(responsible_id)
    return conn.execute(
        "SELECT o.id, o.name, o.reg_no, o.kind, o.responsible_id, u.full_name AS responsible, "
        "(SELECT MAX(i.date) FROM interactions i WHERE i.organization_id = o.id) AS last_interaction, "
        "(SELECT COUNT(*) FROM requests r WHERE r.organization_id = o.id AND r.status != 'Atbildēts') AS open_requests "
        f"FROM organizations o JOIN users u ON u.id = o.responsible_id WHERE {' AND '.join(where)} "
        "ORDER BY o.name COLLATE NOCASE",
        params,
    ).fetchall()


def get(conn: sqlite3.Connection, org_id: int) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT o.*, u.full_name AS responsible FROM organizations o "
        "JOIN users u ON u.id = o.responsible_id WHERE o.id = ?",
        (org_id,),
    ).fetchone()


def card(conn: sqlite3.Connection, org_id: int) -> dict:
    """Kartītes saturs: kontakti (F2), mijiedarbības (F3), pieprasījumi (F4), uzdevumi (F5)."""
    return {
        "contacts": conn.execute(
            "SELECT full_name, position, email, phone, retain_until FROM contacts "
            "WHERE organization_id = ? ORDER BY full_name",
            (org_id,),
        ).fetchall(),
        "interactions": conn.execute(
            "SELECT i.date, i.kind, i.summary, i.next_step, u.full_name AS author FROM interactions i "
            "JOIN users u ON u.id = i.created_by WHERE i.organization_id = ? ORDER BY i.date DESC, i.id DESC",
            (org_id,),
        ).fetchall(),
        "requests": conn.execute(
            "SELECT subject, received, due, status FROM requests WHERE organization_id = ? "
            "ORDER BY status = 'Atbildēts', due",
            (org_id,),
        ).fetchall(),
        "tasks": conn.execute(
            "SELECT t.description, t.due, t.done_at, u.full_name AS assignee FROM tasks t "
            "JOIN users u ON u.id = t.assignee_id WHERE t.organization_id = ? "
            "ORDER BY t.done_at IS NOT NULL, t.due",
            (org_id,),
        ).fetchall(),
    }


def validate(conn: sqlite3.Connection, values: dict, staff_ids: set[int], org_id: int | None = None) -> list[dict]:
    details = []
    if not values["name"]:
        details.append({"field": "name", "issue": "REQUIRED"})
    elif not NAME_MIN <= len(values["name"]) <= NAME_MAX:
        details.append({"field": "name", "issue": "INVALID_LENGTH"})
    if not values["reg_no"]:
        details.append({"field": "reg_no", "issue": "REQUIRED"})
    elif not REG_NO_RE.fullmatch(values["reg_no"]):
        details.append({"field": "reg_no", "issue": "INVALID_FORMAT"})
    elif conn.execute(
        "SELECT 1 FROM organizations WHERE reg_no = ? AND id IS NOT ?", (values["reg_no"], org_id)
    ).fetchone():
        details.append({"field": "reg_no", "issue": "TAKEN"})
    if values["kind"] not in KINDS:
        details.append({"field": "kind", "issue": "REQUIRED"})
    if values["responsible_id"] not in staff_ids:
        details.append({"field": "responsible_id", "issue": "REQUIRED"})
    return details


def read_form(form, user: sqlite3.Row, current_responsible: int | None = None) -> dict:
    """Formas vērtības. Darbinieks atbildīgo nevar izvēlēties: jaunai organizācijai tas ir viņš pats."""
    if user["role"] == "vaditajs":
        raw = form.get("responsible_id", "")
        responsible = int(raw) if raw.isdigit() else None
    else:
        responsible = current_responsible or user["id"]
    return {
        "name": " ".join(form.get("name", "").split()),
        "reg_no": form.get("reg_no", "").replace(" ", ""),
        "kind": form.get("kind", ""),
        "responsible_id": responsible,
    }


def create(conn: sqlite3.Connection, values: dict) -> int:
    cur = conn.execute(
        "INSERT INTO organizations (name, reg_no, kind, responsible_id) VALUES (?, ?, ?, ?)",
        (values["name"], values["reg_no"], values["kind"], values["responsible_id"]),
    )
    conn.commit()
    return cur.lastrowid


def update(conn: sqlite3.Connection, org_id: int, values: dict) -> None:
    conn.execute(
        "UPDATE organizations SET name = ?, reg_no = ?, kind = ?, responsible_id = ? WHERE id = ?",
        (values["name"], values["reg_no"], values["kind"], values["responsible_id"], org_id),
    )
    conn.commit()
