"""Lomu piešķiršana no termināļa, kamēr administratora ekrāna vēl nav (N3).

Lietošana:
    python -m app.roles list
    python -m app.roles set <e-pasts> <darbinieks|vaditajs|administrators>
    python -m app.roles clear <e-pasts>
"""

from __future__ import annotations

import argparse
import os
import sqlite3
import sys
from pathlib import Path

from app import db

ROLE_LABELS = {None: "— gaida apstiprinājumu —", **{r: r for r in db.ROLES}}


def list_users(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute("SELECT id, email, full_name, role FROM users ORDER BY id").fetchall()


def set_role(conn: sqlite3.Connection, email: str, role: str | None) -> bool:
    if role is not None and role not in db.ROLES:
        raise ValueError(f"Nezināma loma: {role}. Atļautās: {', '.join(db.ROLES)}")
    cur = conn.execute("UPDATE users SET role = ? WHERE email = ?", (role, email.strip().lower()))
    conn.commit()
    return cur.rowcount == 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Lietotāju lomu pārvaldība (mācību prototips)")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list", help="Parādīt visus lietotājus un lomas")
    p_set = sub.add_parser("set", help="Piešķirt lomu")
    p_set.add_argument("email")
    p_set.add_argument("role", choices=db.ROLES)
    p_clear = sub.add_parser("clear", help="Noņemt lomu (konts atkal gaida apstiprinājumu)")
    p_clear.add_argument("email")
    args = parser.parse_args(argv)

    conn = db.connect(Path(os.environ.get("APP_DB_PATH", "data/app.db")))

    if args.command == "list":
        rows = list_users(conn)
        if not rows:
            print("Lietotāju nav.")
        for r in rows:
            print(f"{r['id']:>3}  {r['email']:<32} {r['full_name']:<24} {ROLE_LABELS.get(r['role'], r['role'])}")
        return 0

    role = args.role if args.command == "set" else None
    if not set_role(conn, args.email, role):
        print(f"Lietotājs ar e-pastu {args.email} nav atrasts.", file=sys.stderr)
        return 1
    print(f"Gatavs: {args.email} → {ROLE_LABELS[role]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
