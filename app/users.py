"""F0 #6 / N3 · lietotāju lomas: lietotājs lomu pieprasa reģistrācijā, administrators apstiprina."""

from __future__ import annotations

import sqlite3

from app import audit, db


def all_users(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT id, email, full_name, role, requested_role, created_at FROM users ORDER BY role IS NULL DESC, full_name"
    ).fetchall()


def pending(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT id, email, full_name, requested_role, created_at FROM users WHERE role IS NULL ORDER BY created_at"
    ).fetchall()


def staff(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    """Lietotāji, kurus var norādīt kā organizācijas atbildīgo (F1)."""
    return conn.execute(
        "SELECT id, full_name FROM users WHERE role IN ('darbinieks', 'vaditajs') ORDER BY full_name"
    ).fetchall()


def set_role(conn: sqlite3.Connection, admin: sqlite3.Row, user_id: int, role: str) -> str | None:
    """Piešķir vai maina lomu. Atgriež kļūdas tekstu vai None, ja izdevās."""
    if role not in db.ROLES:
        return "Nezināma loma."
    if user_id == admin["id"]:
        return "Savu lomu mainīt nevar, lai neviens nepaliktu bez administratora piekļuves."
    row = conn.execute("SELECT role FROM users WHERE id = ?", (user_id,)).fetchone()
    if row is None:
        return "Lietotājs nav atrasts."
    conn.execute("UPDATE users SET role = ?, requested_role = NULL WHERE id = ?", (role, user_id))
    conn.commit()
    audit.log(conn, admin["id"], "role_approve" if row["role"] is None else "role_change", "user", user_id)
    return None


def reject(conn: sqlite3.Connection, admin: sqlite3.Row, user_id: int) -> str | None:
    """Noraida kontu, kas vēl gaida apstiprinājumu: konts tiek dzēsts (datu minimizācija, N2)."""
    row = conn.execute("SELECT role FROM users WHERE id = ?", (user_id,)).fetchone()
    if row is None:
        return "Lietotājs nav atrasts."
    if row["role"] is not None:
        return "Noraidīt var tikai kontu, kas gaida apstiprinājumu."
    conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    audit.log(conn, admin["id"], "role_reject", "user", user_id)
    return None
