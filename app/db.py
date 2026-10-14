"""SQLite datubāze: lietotāji un sesijas (CR-4/F0), CRM dati vadības panelim (F9)."""

from __future__ import annotations

import sqlite3
from pathlib import Path

ROLES = ("darbinieks", "vaditajs", "administrators")

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    email         TEXT    NOT NULL UNIQUE,
    full_name     TEXT    NOT NULL,
    password_hash TEXT    NOT NULL,
    created_at    TEXT    NOT NULL,
    role          TEXT    CHECK (role IN ('darbinieks', 'vaditajs', 'administrators'))
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
"""


def _migrate(conn: sqlite3.Connection) -> None:
    """CR-4 datubāzēm vēl nav kolonnas `role`."""
    columns = {row["name"] for row in conn.execute("PRAGMA table_info(users)")}
    if "role" not in columns:
        conn.execute("ALTER TABLE users ADD COLUMN role TEXT")
        conn.commit()


def connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)
    _migrate(conn)
    return conn
