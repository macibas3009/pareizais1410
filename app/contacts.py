"""F2 · kontaktpersonas un N2 · glabāšanas termiņš, pārskatīšana, dzēšana pēc pieprasījuma."""

from __future__ import annotations

import re
import sqlite3
from datetime import date, datetime, timezone

from app import accounts, audit, organizations

LEGAL_BASIS = "Līgums"  # vienīgā atļautā vērtība (lēmumu žurnāls, 2026-10-14)
RETENTION_YEARS = 3
PHONE_RE = re.compile(r"^(\+371)?\d{8}$")  # pieņēmums: prasību saraksts, 10. nodaļa, #2
POSITION_MAX = 100
REASON_MAX = 200

FIELD_LABELS = {
    "full_name": "Vārds, uzvārds",
    "position": "Amats",
    "email": "E-pasts",
    "phone": "Tālrunis",
    "basis_date": "Saziņas pamata (līguma) datums",
}
MESSAGES = {
    ("full_name", "REQUIRED"): "Ievadiet vārdu un uzvārdu.",
    ("full_name", "INVALID_FORMAT"): "Vārdā drīkst būt tikai burti, atstarpes, defise un apostrofs.",
    ("position", "REQUIRED"): "Ievadiet amatu.",
    ("position", "TOO_LONG"): f"Amats nedrīkst būt garāks par {POSITION_MAX} rakstzīmēm.",
    ("email", "INVALID_FORMAT"): "Ievadiet derīgu e-pasta adresi, piemēram, vards@example.com.",
    ("email", "ONE_REQUIRED"): "Norādiet e-pastu vai tālruni (vismaz vienu).",
    ("phone", "INVALID_FORMAT"): "Tālrunim jābūt 8 cipariem, var ar +371 priekšā, piemēram, +37120000000.",
    ("basis_date", "REQUIRED"): "Ievadiet līguma vai sadarbības sākuma datumu.",
    ("basis_date", "IN_FUTURE"): "Datums nevar būt nākotnē.",
}


def add_years(d: date, years: int) -> date:
    try:
        return d.replace(year=d.year + years)
    except ValueError:  # 29. februāris
        return d.replace(year=d.year + years, day=28)


def retain_until(conn: sqlite3.Connection, contact_id: int | None, today: date) -> date:
    """Pēdējās mijiedarbības datums + 3 gadi; ja mijiedarbību nav, tad šodiena + 3 gadi (F2).
    Mijiedarbību dalībnieki būs F3; līdz tam termiņš tiek skaitīts no izveides vai labošanas dienas."""
    last = None
    if contact_id is not None and conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'interaction_participants'"
    ).fetchone():
        row = conn.execute(
            "SELECT MAX(i.date) FROM interaction_participants p JOIN interactions i ON i.id = p.interaction_id "
            "WHERE p.contact_id = ?",
            (contact_id,),
        ).fetchone()
        last = date.fromisoformat(row[0]) if row and row[0] else None
    return add_years(last or today, RETENTION_YEARS)


def can_edit(user: sqlite3.Row, contact: sqlite3.Row) -> bool:
    """Kontaktus labo organizācijas atbildīgais vai vadītājs (N3)."""
    return organizations.can_edit(user, contact)


# --- Lasīšana ------------------------------------------------------------------


def get(conn: sqlite3.Connection, contact_id: int) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT c.*, o.name AS organization, o.responsible_id FROM contacts c "
        "JOIN organizations o ON o.id = c.organization_id WHERE c.id = ?",
        (contact_id,),
    ).fetchone()


def to_review(conn: sqlite3.Connection, user: sqlite3.Row, today: date) -> list[sqlite3.Row]:
    """Kontakti ar beigušos glabāšanas termiņu: darbiniekam savējie, vadītājam visi (N2)."""
    where, params = ("1 = 1", ()) if user["role"] == "vaditajs" else ("o.responsible_id = ?", (user["id"],))
    return conn.execute(
        "SELECT c.id, c.full_name, c.position, c.retain_until, o.id AS organization_id, o.name AS organization, "
        "o.responsible_id, u.full_name AS responsible FROM contacts c "
        "JOIN organizations o ON o.id = c.organization_id JOIN users u ON u.id = o.responsible_id "
        f"WHERE c.retain_until < ? AND {where} ORDER BY c.retain_until",
        (today.isoformat(), *params),
    ).fetchall()


def open_deletion_request(conn: sqlite3.Connection, contact_id: int) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT * FROM deletion_requests WHERE contact_id = ? AND status = 'open'", (contact_id,)
    ).fetchone()


def deletion_requests(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT d.id, d.status, d.requested_at, d.handled_at, d.contact_id, c.full_name AS contact, "
        "o.name AS organization, r.full_name AS requested_by, h.full_name AS handled_by "
        "FROM deletion_requests d JOIN organizations o ON o.id = d.organization_id "
        "JOIN users r ON r.id = d.requested_by LEFT JOIN users h ON h.id = d.handled_by "
        "LEFT JOIN contacts c ON c.id = d.contact_id "
        "ORDER BY d.status != 'open', d.requested_at DESC",
    ).fetchall()


def open_deletion_count(conn: sqlite3.Connection) -> int:
    return conn.execute("SELECT COUNT(*) FROM deletion_requests WHERE status = 'open'").fetchone()[0]


# --- Forma ---------------------------------------------------------------------


def read_form(form) -> dict:
    return {
        "full_name": " ".join(form.get("full_name", "").split()),
        "position": " ".join(form.get("position", "").split()),
        "email": accounts.normalize_email(form.get("email", "")),
        "phone": re.sub(r"[\s\-]", "", form.get("phone", "")),
        "basis_date": form.get("basis_date", "").strip(),
    }


def validate(values: dict, today: date) -> list[dict]:
    details = []
    if not values["full_name"]:
        details.append({"field": "full_name", "issue": "REQUIRED"})
    elif not accounts.FULL_NAME_RE.fullmatch(values["full_name"]) or len(values["full_name"]) > 100:
        details.append({"field": "full_name", "issue": "INVALID_FORMAT"})
    if not values["position"]:
        details.append({"field": "position", "issue": "REQUIRED"})
    elif len(values["position"]) > POSITION_MAX:
        details.append({"field": "position", "issue": "TOO_LONG"})
    if not values["email"] and not values["phone"]:
        details.append({"field": "email", "issue": "ONE_REQUIRED"})
    if values["email"] and not accounts.EMAIL_RE.fullmatch(values["email"]):
        details.append({"field": "email", "issue": "INVALID_FORMAT"})
    if values["phone"] and not PHONE_RE.fullmatch(values["phone"]):
        details.append({"field": "phone", "issue": "INVALID_FORMAT"})
    try:
        basis = date.fromisoformat(values["basis_date"])
    except ValueError:
        details.append({"field": "basis_date", "issue": "REQUIRED"})
    else:
        if basis > today:
            details.append({"field": "basis_date", "issue": "IN_FUTURE"})
    return details


# --- Izmaiņas ------------------------------------------------------------------


def create(conn: sqlite3.Connection, user: sqlite3.Row, org_id: int, values: dict, today: date) -> int:
    cur = conn.execute(
        "INSERT INTO contacts (organization_id, full_name, position, email, phone, legal_basis, basis_date, retain_until) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (org_id, values["full_name"], values["position"], values["email"] or None, values["phone"] or None,
         LEGAL_BASIS, values["basis_date"], retain_until(conn, None, today).isoformat()),
    )
    conn.commit()
    audit.log(conn, user["id"], "create", "contact", cur.lastrowid)
    return cur.lastrowid


def update(conn: sqlite3.Connection, user: sqlite3.Row, contact_id: int, values: dict) -> None:
    conn.execute(
        "UPDATE contacts SET full_name = ?, position = ?, email = ?, phone = ?, basis_date = ? WHERE id = ?",
        (values["full_name"], values["position"], values["email"] or None, values["phone"] or None,
         values["basis_date"], contact_id),
    )
    conn.commit()
    audit.log(conn, user["id"], "update", "contact", contact_id)


def extend(conn: sqlite3.Connection, user: sqlite3.Row, contact_id: int, reason: str, today: date) -> str | None:
    """Pagarina glabāšanas termiņu par 3 gadiem no šodienas. Pamatojums obligāts (N2)."""
    reason = " ".join(reason.split())
    if not reason:
        return "Ievadiet pamatojumu, kāpēc kontaktu vajag glabāt ilgāk."
    if len(reason) > REASON_MAX:
        return f"Pamatojums nedrīkst būt garāks par {REASON_MAX} rakstzīmēm."
    new_until = add_years(today, RETENTION_YEARS).isoformat()
    conn.execute("UPDATE contacts SET retain_until = ? WHERE id = ?", (new_until, contact_id))
    conn.execute(
        "INSERT INTO retention_extensions (contact_id, user_id, reason, new_until, at) VALUES (?, ?, ?, ?, ?)",
        (contact_id, user["id"], reason, new_until, _now()),
    )
    conn.commit()
    audit.log(conn, user["id"], "extend", "contact", contact_id)
    return None


def delete(conn: sqlite3.Connection, user: sqlite3.Row, contact_id: int) -> None:
    """Neatgriezeniska dzēšana. Mijiedarbībās dalībnieks kļūst "Dzēsta kontaktpersona" (F3: contact_id → NULL).
    Žurnālā tikai fakts un ID, bez personas datiem."""
    conn.execute("DELETE FROM contacts WHERE id = ?", (contact_id,))
    conn.commit()
    audit.log(conn, user["id"], "delete", "contact", contact_id)


def request_deletion(conn: sqlite3.Connection, user: sqlite3.Row, contact: sqlite3.Row) -> bool:
    if open_deletion_request(conn, contact["id"]):
        return False
    conn.execute(
        "INSERT INTO deletion_requests (contact_id, organization_id, requested_by, requested_at) VALUES (?, ?, ?, ?)",
        (contact["id"], contact["organization_id"], user["id"], _now()),
    )
    conn.commit()
    audit.log(conn, user["id"], "deletion_request", "contact", contact["id"])
    return True


def handle_deletion_request(conn: sqlite3.Connection, admin: sqlite3.Row, request_id: int, approve: bool) -> bool:
    req = conn.execute("SELECT * FROM deletion_requests WHERE id = ? AND status = 'open'", (request_id,)).fetchone()
    if req is None:
        return False
    if approve and req["contact_id"] is not None:
        delete(conn, admin, req["contact_id"])
    conn.execute(
        "UPDATE deletion_requests SET status = ?, handled_by = ?, handled_at = ? WHERE id = ?",
        ("done" if approve else "rejected", admin["id"], _now(), request_id),
    )
    conn.commit()
    if not approve:
        audit.log(conn, admin["id"], "deletion_reject", "contact", req["contact_id"] or 0)
    return True


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
