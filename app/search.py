"""F6 · meklēšana: organizācijas, kontaktpersonas, pieprasījumi. Mijiedarbību teksts netiek meklēts (N2)."""

from __future__ import annotations

import sqlite3

MIN_LENGTH = 2
LIMIT = 50


def _pattern(term: str) -> str:
    escaped = term.casefold().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


def run(conn: sqlite3.Connection, query: str) -> dict | None:
    """Nejutīga pret lielajiem un mazajiem burtiem; garumzīmes jāievada (ā ≠ a). None, ja vaicājums par īsu."""
    term = " ".join(query.split())
    if len(term) < MIN_LENGTH:
        return None
    like = _pattern(term)
    return {
        "organizations": conn.execute(
            "SELECT o.id, o.name, o.reg_no, o.kind, u.full_name AS responsible FROM organizations o "
            "JOIN users u ON u.id = o.responsible_id "
            "WHERE lv_lower(o.name) LIKE ? ESCAPE '\\' OR o.reg_no LIKE ? ESCAPE '\\' ORDER BY o.name LIMIT ?",
            (like, like, LIMIT),
        ).fetchall(),
        # Rezultātā nav e-pasta un tālruņa (minimizācija); tie ir kartītē, kuras atvēršana tiek žurnalēta
        "contacts": conn.execute(
            "SELECT c.id, c.full_name, c.position, o.id AS organization_id, o.name AS organization FROM contacts c "
            "JOIN organizations o ON o.id = c.organization_id "
            "WHERE lv_lower(c.full_name) LIKE ? ESCAPE '\\' OR lv_lower(c.email) LIKE ? ESCAPE '\\' "
            "ORDER BY c.full_name LIMIT ?",
            (like, like, LIMIT),
        ).fetchall(),
        "requests": conn.execute(
            "SELECT r.id, r.subject, r.status, r.due, o.id AS organization_id, o.name AS organization FROM requests r "
            "JOIN organizations o ON o.id = r.organization_id "
            "WHERE lv_lower(r.subject) LIKE ? ESCAPE '\\' ORDER BY r.status = 'Atbildēts', r.due LIMIT ?",
            (like, LIMIT),
        ).fetchall(),
    }
