"""F9 · vadības panelis. Sākumdati ir sintētiski (app/seed.py)."""

import re
from datetime import date

import pytest
from fastapi.testclient import TestClient

from app import db, seed
from app.dashboard import due_label, plural
from app.main import create_app


@pytest.fixture
def db_path(tmp_path):
    path = tmp_path / "test.db"
    seed.seed(db.connect(path))
    return path


@pytest.fixture
def client(db_path):
    return TestClient(create_app(db_path=db_path))


def login(client, email):
    res = client.post("/auth/login", json={"email": email, "password": seed.SEED_PASSWORD})
    assert res.status_code == 200


def stat(html, label):
    match = re.search(r'stat-value">(\d+)</span> <span class="stat-label">' + label, html)
    assert match, f"Nav kartes: {label}"
    return int(match.group(1))


# 1
def test_panel_requires_session(client):
    res = client.get("/panelis", follow_redirects=False)
    assert res.status_code == 303
    assert res.headers["location"] == "/login"


def test_old_profile_url_redirects_to_panel(client):
    res = client.get("/profile", follow_redirects=False)
    assert res.headers["location"] == "/panelis"


# 2, 4
def test_employee_sees_all_blocks(client):
    login(client, "darbinieks@example.com")
    html = client.get("/panelis").text
    assert "Labdien, Anna!" in html
    for heading in ("Uzdevumi šodien", "Kavētie un tuvojošies pieprasījumi", "Pēdējās mijiedarbības"):
        assert f">{heading}</h2>" in html
    assert "<caption" in html and 'scope="col"' in html


# 3: statuss ir teksts, ne tikai krāsa
def test_overdue_and_upcoming_are_text(client):
    login(client, "darbinieks@example.com")
    html = client.get("/panelis").text
    assert "KAVĒTS (10 d.)" in html
    assert "Termiņš pēc 2 d." in html
    assert "Nokavēts" in html


# 5: darbinieks redz tikai savas organizācijas, vadītājs visu iestādi
def test_employee_scope_is_own_organizations(client):
    login(client, "darbinieks@example.com")
    html = client.get("/panelis").text
    assert stat(html, "manas organizācijas") == 4
    assert "SIA Ezerkrasta Būve" in html
    assert "Nodibinājums Laivu Skola" not in html  # cita darbinieka organizācija


def test_manager_sees_whole_institution(client):
    login(client, "vaditajs@example.com")
    html = client.get("/panelis").text
    assert stat(html, "organizācijas iestādē") == 10
    assert "Nodibinājums Laivu Skola" in html
    assert stat(html, "kontakti jāpārskata") == 3


def test_admin_sees_pending_users(client):
    client.post("/auth/register", json={"email": "jauns@example.com", "fullName": "Jauns Lietotājs", "password": "drosa-parole-123"})
    login(client, "admin@example.com")
    html = client.get("/panelis").text
    assert "Lietotāji, kas gaida lomu" in html
    assert "jauns@example.com" in html


def test_new_user_without_role_sees_pending_notice(client):
    client.post("/auth/register", json={"email": "jauns@example.com", "fullName": "Jauns Lietotājs", "password": "drosa-parole-123"})
    client.post("/auth/login", json={"email": "jauns@example.com", "password": "drosa-parole-123"})
    html = client.get("/panelis").text
    assert "Konts gaida apstiprinājumu" in html
    assert "SIA Ezerkrasta Būve" not in html


# 4: tukšs bloks
def test_empty_block_message(client):
    login(client, "darbinieks@example.com")
    html = client.get("/panelis").text
    ids = re.findall(r'action="/uzdevumi/(\d+)/izpildits"', html)
    for task_id in ids:
        client.post(f"/uzdevumi/{task_id}/izpildits")
    assert "Šodien uzdevumu nav." in client.get("/panelis").text


# 7: bez JavaScript — uzdevuma izpilde un iziešana ar parastām formām
def test_complete_task_with_form(client):
    login(client, "darbinieks@example.com")
    html = client.get("/panelis").text
    before = stat(html, "uzdevumi šodien")
    task_id = re.search(r'action="/uzdevumi/(\d+)/izpildits"', html).group(1)

    res = client.post(f"/uzdevumi/{task_id}/izpildits", follow_redirects=False)
    assert res.status_code == 303
    assert stat(client.get("/panelis").text, "uzdevum(?:s|i) šodien") == before - 1


def test_cannot_complete_colleagues_task(client):
    login(client, "vaditajs@example.com")
    html = client.get("/panelis").text
    # Mārtiņa uzdevums "Saskaņot mācību programmu" ir redzams vadītājam
    ids = re.findall(r'action="/uzdevumi/(\d+)/izpildits"', html)
    client.post("/iziet")
    login(client, "darbinieks@example.com")
    own = set(re.findall(r'action="/uzdevumi/(\d+)/izpildits"', client.get("/panelis").text))
    foreign = next(i for i in ids if i not in own)
    assert client.post(f"/uzdevumi/{foreign}/izpildits").status_code == 404


def test_logout_form_without_js(client):
    login(client, "darbinieks@example.com")
    res = client.post("/iziet", follow_redirects=False)
    assert res.status_code == 303
    assert res.headers["location"] == "/login"
    assert client.get("/panelis", follow_redirects=False).status_code == 303


def test_panel_has_no_scripts(client):
    login(client, "darbinieks@example.com")
    assert "<script" not in client.get("/panelis").text


def test_seed_matches_n4_counts(db_path):
    conn = db.connect(db_path)
    count = lambda table: conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]  # noqa: E731
    assert (count("organizations"), count("contacts"), count("interactions")) == (10, 20, 30)
    assert seed.seed(conn) is False  # atkārtota palaišana neko nedublē


def test_due_label_and_plural():
    today = date(2026, 10, 14)
    assert due_label("2026-10-11", today) == ("KAVĒTS (3 d.)", "late")
    assert due_label("2026-10-14", today) == ("Termiņš šodien", "soon")
    assert due_label("2026-10-16", today) == ("Termiņš pēc 2 d.", "upcoming")
    assert plural(1, "a", "b") == "a" and plural(11, "a", "b") == "b" and plural(21, "a", "b") == "a"
