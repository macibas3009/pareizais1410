"""Sintētiski sākumdati (N4): lietotāji ar lomām, 10 organizācijas, 20 kontakti, 30 mijiedarbības.

Visi vārdi, uzņēmumi un reģistrācijas numuri ir izdomāti. Datumi tiek rēķināti
no šodienas, lai vadības panelī (F9) vienmēr būtu kavēti un tuvojošies termiņi.

Palaišana: `make seed`
"""

from __future__ import annotations

import os
import sqlite3
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from app import db, security

# Testa parole visiem sākumdatu lietotājiem. Tikai lokālai mācību videi;
# jebkurā koplietotā vidē uzdod citu ar vides mainīgo SEED_PASSWORD.
SEED_PASSWORD = os.environ.get("SEED_PASSWORD", "Ezermala-2026!")

USERS = [
    # (atslēga, e-pasts, vārds, loma)
    ("anna", "darbinieks@example.com", "Anna Kalniņa", "darbinieks"),
    ("martins", "darbinieks2@example.com", "Mārtiņš Ozols", "darbinieks"),
    ("ilze", "vaditajs@example.com", "Ilze Bērziņa", "vaditajs"),
    ("admin", "admin@example.com", "Kārlis Liepa", "administrators"),
]

ORGANIZATIONS = [
    # (nosaukums, reģ. nr., veids, atbildīgais)
    ("SIA Ezerkrasta Būve", "40003000001", "Uzņēmums", "anna"),
    ("Biedrība Zaļais Krasts", "40008000002", "NVO", "anna"),
    ("Ezermalas novada pašvaldība", "90000000003", "Pašvaldība", "anna"),
    ("SIA Niedru Tehnoloģijas", "40003000004", "Uzņēmums", "anna"),
    ("Nodibinājums Laivu Skola", "40008000005", "NVO", "martins"),
    ("SIA Krasta Loģistika", "40003000006", "Uzņēmums", "martins"),
    ("Kalnāju pagasta pārvalde", "90000000007", "Pašvaldība", "martins"),
    ("Biedrība Ezera Draugi", "40008000008", "NVO", "martins"),
    ("SIA Saulrieta Digitālā", "40003000009", "Uzņēmums", "ilze"),
    ("Upesmalas novada pašvaldība", "90000000010", "Pašvaldība", "ilze"),
]

CONTACT_NAMES = [
    ("Jānis Bērziņš", "Valdes loceklis"), ("Līga Ozoliņa", "Projektu vadītāja"),
    ("Pēteris Kalns", "Valdes priekšsēdētājs"), ("Dace Liepiņa", "Koordinatore"),
    ("Edgars Sniedze", "Attīstības nodaļas vadītājs"), ("Inese Vītola", "Speciāliste"),
    ("Raimonds Egle", "Izpilddirektors"), ("Santa Krūmiņa", "Mārketinga vadītāja"),
    ("Toms Lazdiņš", "Direktors"), ("Agnese Priede", "Pasniedzēja"),
    ("Valdis Ābele", "Loģistikas vadītājs"), ("Kristīne Celma", "Grāmatvede"),
    ("Juris Avotiņš", "Pārvaldes vadītājs"), ("Elīna Rozīte", "Sekretāre"),
    ("Andris Mežs", "Valdes loceklis"), ("Laura Dzirne", "Brīvprātīgo koordinatore"),
    ("Oskars Bite", "Tehniskais direktors"), ("Zane Kļava", "Pārdošanas vadītāja"),
    ("Ivars Strauts", "Izpilddirektors"), ("Maija Smilga", "Plānošanas speciāliste"),
]

INTERACTION_TEXTS = [
    ("Sanāksme", "Apspriests kopīgs seminārs par krasta joslas apsaimniekošanu. Vienojāmies par datumu novembrī.", "Nosūtīt semināra programmas projektu"),
    ("Zvans", "Organizācija jautāja par konsultāciju par ES fondu projektu. Sniegta sākotnējā informācija.", "Nosūtīt konsultāciju grafiku"),
    ("E-pasts", "Saņemts precizēts sadarbības līguma projekts. Nepieciešami juristu komentāri.", "Pārsūtīt juridiskajai nodaļai"),
    ("Sanāksme", "Tikšanās par pieprasījuma statusu. Organizācija apmierināta ar progresu.", None),
    ("Zvans", "Precizēti dalībnieku skaits un telpu prasības pasākumam.", "Rezervēt zāli"),
    ("E-pasts", "Nosūtīta atbilde uz pieprasījumu par datu apmaiņu. Gaidām apstiprinājumu.", None),
]

REQUESTS = [
    # (organizācijas indekss, temats, saņemts pirms N d., termiņš pēc N d. (negatīvs = kavēts), statuss)
    (0, "Būvatļaujas konsultācija krasta zonā", 40, -10, "Darbā"),
    (1, "Atbalsts talkas organizēšanai", 25, 5, "Jauns"),
    (2, "Datu apmaiņas līguma saskaņošana", 33, -3, "Jauns"),
    (3, "Informācija par inovāciju granta konkursu", 10, 20, "Darbā"),
    (0, "Semināra telpu pieprasījums", 28, 2, "Darbā"),
    (4, "Mācību programmas saskaņošana", 35, -5, "Darbā"),
    (5, "Ostas piekļuves saskaņojums", 20, 6, "Jauns"),
    (6, "Kopīga projekta pieteikums", 15, 15, "Jauns"),
    (7, "Vides monitoringa dati", 45, -14, "Jauns"),
    (8, "Digitālās platformas demonstrācija", 12, 1, "Darbā"),
    (9, "Sadarbības memoranda projekts", 30, 0, "Darbā"),
    (2, "Iedzīvotāju aptaujas rezultāti", 60, -30, "Atbildēts"),
]

TASKS = [
    # (apraksts, izpildītājs, termiņš pēc N d., organizācijas indekss, izpildīts)
    ("Nosūtīt semināra programmas projektu", "anna", -2, 0, False),
    ("Piezvanīt par talkas datumu", "anna", 0, 1, False),
    ("Sagatavot datu apmaiņas līguma komentārus", "anna", 0, 2, False),
    ("Pārbaudīt granta nolikumu", "anna", 3, 3, False),
    ("Rezervēt zāli semināram", "anna", -1, 0, True),
    ("Saskaņot mācību programmu", "martins", -1, 4, False),
    ("Atbildēt par ostas piekļuvi", "martins", 0, 5, False),
    ("Sagatavot memoranda projektu", "ilze", 0, 9, False),
    ("Sagatavot ceturkšņa pārskatu", "ilze", 5, None, False),
    ("Atjaunot vides monitoringa datus", "martins", 2, 7, False),
]


def seed(conn: sqlite3.Connection, today: date | None = None) -> bool:
    """Ievieto sākumdatus. Atgriež False, ja tie jau ir ievietoti."""
    today = today or date.today()
    if conn.execute("SELECT 1 FROM organizations LIMIT 1").fetchone():
        return False

    now = datetime.now(timezone.utc).isoformat()
    password_hash = security.hash_password(SEED_PASSWORD)
    user_ids: dict[str, int] = {}
    for key, email, name, role in USERS:
        row = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if row:
            conn.execute("UPDATE users SET role = ? WHERE id = ?", (role, row["id"]))
            user_ids[key] = row["id"]
        else:
            cur = conn.execute(
                "INSERT INTO users (email, full_name, password_hash, created_at, role) VALUES (?, ?, ?, ?, ?)",
                (email, name, password_hash, now, role),
            )
            user_ids[key] = cur.lastrowid

    org_ids = []
    for name, reg_no, kind, owner in ORGANIZATIONS:
        cur = conn.execute(
            "INSERT INTO organizations (name, reg_no, kind, responsible_id) VALUES (?, ?, ?, ?)",
            (name, reg_no, kind, user_ids[owner]),
        )
        org_ids.append(cur.lastrowid)

    # 2 kontakti katrai organizācijai; 3 kontaktiem glabāšanas termiņš ir beidzies (N2 "Jāpārskata")
    expired = {1, 6, 13}
    for i, (name, position) in enumerate(CONTACT_NAMES):
        org_index = i // 2
        basis = today - timedelta(days=400 + i * 30)
        retain = today - timedelta(days=10 + i) if i in expired else today + timedelta(days=3 * 365 - i * 20)
        email = f"kontakts{i + 1}@example.com"
        conn.execute(
            "INSERT INTO contacts (organization_id, full_name, position, email, basis_date, retain_until) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (org_ids[org_index], name, position, email, basis.isoformat(), retain.isoformat()),
        )

    # 30 mijiedarbības, 3 katrai organizācijai, pēdējo 60 dienu laikā
    for i in range(30):
        org_index = i % 10
        kind, summary, next_step = INTERACTION_TEXTS[i % len(INTERACTION_TEXTS)]
        owner = ORGANIZATIONS[org_index][3]
        conn.execute(
            "INSERT INTO interactions (organization_id, kind, date, summary, next_step, created_by) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (org_ids[org_index], kind, (today - timedelta(days=i * 2)).isoformat(), summary, next_step, user_ids[owner]),
        )

    for org_index, subject, received_ago, due_in, status in REQUESTS:
        conn.execute(
            "INSERT INTO requests (organization_id, subject, received, due, status) VALUES (?, ?, ?, ?, ?)",
            (
                org_ids[org_index],
                subject,
                (today - timedelta(days=received_ago)).isoformat(),
                (today + timedelta(days=due_in)).isoformat(),
                status,
            ),
        )

    for description, assignee, due_in, org_index, done in TASKS:
        conn.execute(
            "INSERT INTO tasks (description, assignee_id, created_by, due, organization_id, done_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                description,
                user_ids[assignee],
                user_ids["ilze"],
                (today + timedelta(days=due_in)).isoformat(),
                org_ids[org_index] if org_index is not None else None,
                now if done else None,
            ),
        )

    conn.commit()
    return True


if __name__ == "__main__":
    path = Path(os.environ.get("APP_DB_PATH", "data/app.db"))
    inserted = seed(db.connect(path))
    print("Sākumdati ievietoti" if inserted else "Sākumdati jau ir datubāzē", file=sys.stderr)
