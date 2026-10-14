"""F3 · mijiedarbību žurnāls: zvans, e-pasts vai sanāksme ar dalībniekiem, kopsavilkumu un nākamo soli."""

from __future__ import annotations

import sqlite3
from datetime import date

from app import audit, contacts

KINDS = ("Zvans", "E-pasts", "Sanāksme")
SUMMARY_MAX = 2000
NEXT_STEP_MAX = 500
DELETED_CONTACT = "Dzēsta kontaktpersona"

FIELD_LABELS = {
    "kind": "Veids",
    "date": "Datums",
    "participants": "Dalībnieki",
    "summary": "Kopsavilkums",
    "next_step": "Nākamais solis",
}
MESSAGES = {
    ("kind", "REQUIRED"): "Izvēlieties mijiedarbības veidu.",
    ("date", "REQUIRED"): "Ievadiet datumu.",
    ("date", "IN_FUTURE"): "Datums nevar būt nākotnē.",
    ("participants", "REQUIRED"): "Atzīmējiet vismaz vienu dalībnieku.",
    ("summary", "REQUIRED"): "Ievadiet kopsavilkumu vai izveidojiet to ar MI.",
    ("summary", "TOO_LONG"): f"Kopsavilkums nedrīkst būt garāks par {SUMMARY_MAX} rakstzīmēm.",
    ("next_step", "TOO_LONG"): f"Nākamais solis nedrīkst būt garāks par {NEXT_STEP_MAX} rakstzīmēm.",
}


def participant_names_sql(alias: str = "i") -> str:
    """Dalībnieku vārdi vienā tekstā; dzēsta kontaktpersona tiek parādīta anonīmi (N2)."""
    return (
        "(SELECT GROUP_CONCAT(name, ', ') FROM ("
        "SELECT CASE WHEN p.kind = 'contact' THEN COALESCE(c.full_name, '" + DELETED_CONTACT + "') "
        "ELSE u.full_name END AS name FROM interaction_participants p "
        "LEFT JOIN contacts c ON c.id = p.contact_id LEFT JOIN users u ON u.id = p.user_id "
        f"WHERE p.interaction_id = {alias}.id ORDER BY p.kind, name))"
    )


def for_organization(conn: sqlite3.Connection, org_id: int) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT i.id, i.date, i.kind, i.summary, i.next_step, i.ai_source, u.full_name AS author, "
        f"a.full_name AS approved_by, {participant_names_sql()} AS participants "
        "FROM interactions i JOIN users u ON u.id = i.created_by LEFT JOIN users a ON a.id = i.approved_by "
        "WHERE i.organization_id = ? ORDER BY i.date DESC, i.id DESC",
        (org_id,),
    ).fetchall()


def options(conn: sqlite3.Connection, org_id: int) -> tuple[list[sqlite3.Row], list[sqlite3.Row]]:
    """Kontaktpersonas no šīs organizācijas un darbinieki, ko var atzīmēt kā dalībniekus."""
    org_contacts = conn.execute(
        "SELECT id, full_name, position FROM contacts WHERE organization_id = ? ORDER BY full_name", (org_id,)
    ).fetchall()
    staff = conn.execute(
        "SELECT id, full_name FROM users WHERE role IN ('darbinieks', 'vaditajs') ORDER BY full_name"
    ).fetchall()
    return org_contacts, staff


def read_form(form) -> dict:
    def ids(name: str) -> list[int]:
        return sorted({int(v) for v in form.getlist(name) if v.isdigit()})

    ai_source = form.get("ai_source", "")
    return {
        "kind": form.get("kind", ""),
        "date": form.get("date", "").strip(),
        "contact_ids": ids("contacts"),
        "staff_ids": ids("staff"),
        "notes": form.get("notes", ""),
        "summary": form.get("summary", "").strip(),
        "next_step": " ".join(form.get("next_step", "").split()),
        "ai_source": ai_source if ai_source in ("claude", "imitacija") else "",
    }


def validate(values: dict, contact_ids: set[int], staff_ids: set[int], today: date) -> list[dict]:
    details = []
    if values["kind"] not in KINDS:
        details.append({"field": "kind", "issue": "REQUIRED"})
    try:
        if date.fromisoformat(values["date"]) > today:
            details.append({"field": "date", "issue": "IN_FUTURE"})
    except ValueError:
        details.append({"field": "date", "issue": "REQUIRED"})
    chosen_contacts = [c for c in values["contact_ids"] if c in contact_ids]
    chosen_staff = [s for s in values["staff_ids"] if s in staff_ids]
    if not chosen_contacts and not chosen_staff:
        details.append({"field": "participants", "issue": "REQUIRED"})
    if not values["summary"]:
        details.append({"field": "summary", "issue": "REQUIRED"})
    elif len(values["summary"]) > SUMMARY_MAX:
        details.append({"field": "summary", "issue": "TOO_LONG"})
    if len(values["next_step"]) > NEXT_STEP_MAX:
        details.append({"field": "next_step", "issue": "TOO_LONG"})
    values["contact_ids"], values["staff_ids"] = chosen_contacts, chosen_staff
    return details


def create(conn: sqlite3.Connection, user: sqlite3.Row, org_id: int, values: dict, today: date) -> int:
    """Saglabā mijiedarbību. MI kopsavilkums tiek saglabāts kā darbinieka apstiprināts (MI-1).
    Brīvais teksts (piezīmes) netiek saglabāts (N2 minimizācija)."""
    ai_source = values["ai_source"] or None
    cur = conn.execute(
        "INSERT INTO interactions (organization_id, kind, date, summary, next_step, created_by, ai_source, approved_by) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (org_id, values["kind"], values["date"], values["summary"], values["next_step"] or None, user["id"],
         ai_source, user["id"] if ai_source else None),
    )
    interaction_id = cur.lastrowid
    conn.executemany(
        "INSERT INTO interaction_participants (interaction_id, kind, contact_id) VALUES (?, 'contact', ?)",
        [(interaction_id, c) for c in values["contact_ids"]],
    )
    conn.executemany(
        "INSERT INTO interaction_participants (interaction_id, kind, user_id) VALUES (?, 'staff', ?)",
        [(interaction_id, s) for s in values["staff_ids"]],
    )
    # F2: "glabāt līdz" = pēdējā mijiedarbība + 3 gadi katram dalībniekam
    for contact_id in values["contact_ids"]:
        conn.execute(
            "UPDATE contacts SET retain_until = ? WHERE id = ?",
            (contacts.retain_until(conn, contact_id, today).isoformat(), contact_id),
        )
    conn.commit()
    audit.log(conn, user["id"], "create", "interaction", interaction_id)
    if ai_source:
        audit.log(conn, user["id"], "ai_approve", "interaction", interaction_id)
    return interaction_id
