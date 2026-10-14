"""F9 · vadības paneļa dati un formatēšana. HTML ir šablonā templates/panelis.html."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import date, timedelta

ROLE_LABELS = {
    "darbinieks": "Darbinieks",
    "vaditajs": "Vadītājs",
    "administrators": "Administrators",
}
WEEKDAYS = ["pirmdiena", "otrdiena", "trešdiena", "ceturtdiena", "piektdiena", "sestdiena", "svētdiena"]
MONTHS = [
    "janvāris", "februāris", "marts", "aprīlis", "maijs", "jūnijs",
    "jūlijs", "augusts", "septembris", "oktobris", "novembris", "decembris",
]
UPCOMING_DAYS = 7
LIST_LIMIT = 5


# --- Dati ----------------------------------------------------------------------


@dataclass
class Scope:
    """Darbinieks redz savas organizācijas, vadītājs visu iestādi (N3)."""

    user_id: int
    whole_institution: bool

    def org_filter(self, column: str = "o.responsible_id") -> tuple[str, tuple]:
        if self.whole_institution:
            return "1 = 1", ()
        return f"{column} = ?", (self.user_id,)


def stats(conn: sqlite3.Connection, scope: Scope, today: date) -> dict[str, int]:
    where, params = scope.org_filter()
    t = today.isoformat()
    task_where = "1 = 1" if scope.whole_institution else "t.assignee_id = ?"
    task_params = () if scope.whole_institution else (scope.user_id,)
    return {
        "organizations": conn.execute(
            f"SELECT COUNT(*) FROM organizations o WHERE {where}", params
        ).fetchone()[0],
        "open_requests": conn.execute(
            f"SELECT COUNT(*) FROM requests r JOIN organizations o ON o.id = r.organization_id "
            f"WHERE r.status != 'Atbildēts' AND {where}",
            params,
        ).fetchone()[0],
        "contacts_to_review": conn.execute(
            f"SELECT COUNT(*) FROM contacts c JOIN organizations o ON o.id = c.organization_id "
            f"WHERE c.retain_until < ? AND {where}",
            (t, *params),
        ).fetchone()[0],
        "tasks_today": conn.execute(
            f"SELECT COUNT(*) FROM tasks t WHERE t.done_at IS NULL AND t.due <= ? AND {task_where}",
            (t, *task_params),
        ).fetchone()[0],
    }


def tasks_today(conn: sqlite3.Connection, scope: Scope, today: date) -> list[sqlite3.Row]:
    task_where = "1 = 1" if scope.whole_institution else "t.assignee_id = ?"
    task_params = () if scope.whole_institution else (scope.user_id,)
    return conn.execute(
        f"SELECT t.id, t.description, t.due, t.assignee_id, u.full_name AS assignee, o.name AS organization "
        f"FROM tasks t JOIN users u ON u.id = t.assignee_id "
        f"LEFT JOIN organizations o ON o.id = t.organization_id "
        f"WHERE t.done_at IS NULL AND t.due <= ? AND {task_where} "
        f"ORDER BY t.due, t.id LIMIT ?",
        (today.isoformat(), *task_params, LIST_LIMIT),
    ).fetchall()


def urgent_requests(conn: sqlite3.Connection, scope: Scope, today: date) -> list[sqlite3.Row]:
    where, params = scope.org_filter()
    horizon = (today + timedelta(days=UPCOMING_DAYS)).isoformat()
    return conn.execute(
        f"SELECT r.id, r.subject, r.due, r.status, o.name AS organization "
        f"FROM requests r JOIN organizations o ON o.id = r.organization_id "
        f"WHERE r.status != 'Atbildēts' AND r.due <= ? AND {where} "
        f"ORDER BY r.due, r.id",
        (horizon, *params),
    ).fetchall()


def recent_interactions(conn: sqlite3.Connection, scope: Scope) -> list[sqlite3.Row]:
    where, params = scope.org_filter()
    return conn.execute(
        f"SELECT i.date, i.kind, i.summary, o.name AS organization "
        f"FROM interactions i JOIN organizations o ON o.id = i.organization_id "
        f"WHERE {where} ORDER BY i.date DESC, i.id DESC LIMIT ?",
        (*params, LIST_LIMIT),
    ).fetchall()


def pending_users(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT full_name, email, created_at FROM users WHERE role IS NULL ORDER BY created_at"
    ).fetchall()


def complete_task(conn: sqlite3.Connection, task_id: int, user: sqlite3.Row, now: str) -> bool:
    """Atzīmē uzdevumu kā izpildītu. Darbinieks var tikai savus, vadītājs jebkuru."""
    row = conn.execute("SELECT assignee_id FROM tasks WHERE id = ? AND done_at IS NULL", (task_id,)).fetchone()
    if row is None:
        return False
    if user["role"] != "vaditajs" and row["assignee_id"] != user["id"]:
        return False
    conn.execute("UPDATE tasks SET done_at = ? WHERE id = ?", (now, task_id))
    conn.commit()
    return True


# --- Formatēšana ---------------------------------------------------------------


def fmt_date(value: str) -> str:
    d = date.fromisoformat(value[:10])
    return f"{d.day:02d}.{d.month:02d}.{d.year}"


def long_date(d: date) -> str:
    return f"{WEEKDAYS[d.weekday()].capitalize()}, {d.year}. gada {d.day}. {MONTHS[d.month - 1]}"


def due_label(due: str, today: date) -> tuple[str, str]:
    """Termiņa teksts un CSS klase. Statuss vienmēr ir izteikts ar tekstu, ne tikai krāsu (N1)."""
    days = (date.fromisoformat(due) - today).days
    if days < 0:
        return f"KAVĒTS ({-days} d.)", "late"
    if days == 0:
        return "Termiņš šodien", "soon"
    return f"Termiņš pēc {days} d.", "upcoming"


def first_sentence(text: str) -> str:
    head, sep, _ = text.partition(". ")
    return head + ("." if sep else "")


def plural(n: int, one: str, many: str) -> str:
    # Latviešu valodā vienskaitlis, ja skaitlis beidzas ar 1, bet ne ar 11
    return one if n % 10 == 1 and n % 100 != 11 else many


# --- Šablona konteksts -------------------------------------------------------


def context(conn: sqlite3.Connection, user: sqlite3.Row, today: date) -> dict:
    """Dati šablonam panelis.html atbilstoši lietotāja lomai (N3)."""
    role = user["role"]
    if role is None:
        return {"view": "pending"}
    if role == "administrators":
        return {"view": "admin", "pending_users": pending_users(conn)}
    whole = role == "vaditajs"
    scope = Scope(user_id=user["id"], whole_institution=whole)
    return {
        "view": "crm",
        "whole_institution": whole,
        "stats": stats(conn, scope, today),
        "tasks": tasks_today(conn, scope, today),
        "requests": urgent_requests(conn, scope, today),
        "interactions": recent_interactions(conn, scope),
        "upcoming_days": UPCOMING_DAYS,
    }
