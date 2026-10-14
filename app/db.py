"""SQLite datubāze: lietotāji un sesijas (CR-4/F0), CRM dati vadības panelim (F9)."""

from __future__ import annotations

import sqlite3
from pathlib import Path

ROLES = ("darbinieks", "vaditajs", "administrators")
REQUESTABLE_ROLES = ("darbinieks", "vaditajs")  # administratora lomu reģistrācijā pieprasīt nevar

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    email         TEXT    NOT NULL UNIQUE,
    full_name     TEXT    NOT NULL,
    password_hash TEXT    NOT NULL,
    created_at    TEXT    NOT NULL,
    role          TEXT    CHECK (role IN ('darbinieks', 'vaditajs', 'administrators')),
    requested_role TEXT   CHECK (requested_role IN ('darbinieks', 'vaditajs'))
);

CREATE TABLE IF NOT EXISTS sessions (
    token_hash TEXT    PRIMARY KEY,
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    expires_at TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS organizations (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    name           TEXT    NOT NULL,
    reg_no         TEXT    NOT NULL UNIQUE,
    kind           TEXT    NOT NULL CHECK (kind IN ('Uzņēmums', 'NVO', 'Pašvaldība')),
    responsible_id INTEGER NOT NULL REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS contacts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    full_name       TEXT    NOT NULL,
    position        TEXT    NOT NULL,
    email           TEXT,
    phone           TEXT,
    legal_basis     TEXT    NOT NULL DEFAULT 'Līgums',
    basis_date      TEXT    NOT NULL,
    retain_until    TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS interactions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    kind            TEXT    NOT NULL CHECK (kind IN ('Zvans', 'E-pasts', 'Sanāksme')),
    date            TEXT    NOT NULL,
    summary         TEXT    NOT NULL,
    next_step       TEXT,
    created_by      INTEGER NOT NULL REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS requests (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    subject         TEXT    NOT NULL,
    received        TEXT    NOT NULL,
    due             TEXT    NOT NULL,
    status          TEXT    NOT NULL CHECK (status IN ('Jauns', 'Darbā', 'Atbildēts'))
);

CREATE TABLE IF NOT EXISTS tasks (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    description     TEXT    NOT NULL,
    assignee_id     INTEGER NOT NULL REFERENCES users(id),
    created_by      INTEGER NOT NULL REFERENCES users(id),
    due             TEXT    NOT NULL,
    organization_id INTEGER REFERENCES organizations(id),
    request_id      INTEGER REFERENCES requests(id),
    done_at         TEXT
);

-- N2 · kontaktpersonas dzēšana pēc tās pieprasījuma (izpilda administrators)
CREATE TABLE IF NOT EXISTS deletion_requests (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    contact_id      INTEGER REFERENCES contacts(id) ON DELETE SET NULL,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    requested_by    INTEGER NOT NULL REFERENCES users(id),
    requested_at    TEXT    NOT NULL,
    status          TEXT    NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'done', 'rejected')),
    handled_by      INTEGER REFERENCES users(id),
    handled_at      TEXT
);

-- N2 · glabāšanas termiņa pagarinājumi ar pamatojumu
CREATE TABLE IF NOT EXISTS retention_extensions (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    contact_id INTEGER REFERENCES contacts(id) ON DELETE SET NULL,
    user_id    INTEGER NOT NULL REFERENCES users(id),
    reason     TEXT    NOT NULL,
    new_until  TEXT    NOT NULL,
    at         TEXT    NOT NULL
);

-- N2 · piekļuves žurnāls: kas, ko, kad. Bez personas datiem, tikai ID
CREATE TABLE IF NOT EXISTS access_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(id),
    action      TEXT    NOT NULL,
    object_type TEXT    NOT NULL,
    object_id   INTEGER NOT NULL,
    at          TEXT    NOT NULL
);
"""


def _migrate(conn: sqlite3.Connection) -> None:
    """Agrākām datubāzēm trūkst kolonnu `role` (CR-4) un `requested_role` (F0 #6)."""
    columns = {row["name"] for row in conn.execute("PRAGMA table_info(users)")}
    for column in ("role", "requested_role"):
        if column not in columns:
            conn.execute(f"ALTER TABLE users ADD COLUMN {column} TEXT")
    conn.commit()


def open_db(path: Path) -> sqlite3.Connection:
    """Savienojums vienam pieprasījumam (Flask `g`), bez shēmas izveides."""
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def connect(path: Path) -> sqlite3.Connection:
    """Izveido datubāzi, ja tās nav, un atjauno shēmu. Izsauc lietotnes startā un skriptos."""
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = open_db(path)
    conn.executescript(SCHEMA)
    _migrate(conn)
    return conn
