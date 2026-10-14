"""F4 · pieprasījumi un F5 · uzdevumi."""

import re
from datetime import date, timedelta

import pytest

from app import db, org_requests, seed
from app.main import create_app

HTML = {"Accept": "text/html"}
TODAY = date.today()


@pytest.fixture
def db_path(tmp_path):
    path = tmp_path / "test.db"
    seed.seed(db.connect(path))
    return path


@pytest.fixture
def client(db_path):
    return create_app(db_path=db_path).test_client()


def login(client, email="darbinieks@example.com"):
    assert client.post("/login", data={"email": email, "password": seed.SEED_PASSWORD}, headers=HTML).status_code == 303


def q(db_path, sql, *params):
    return db.connect(db_path).execute(sql, params).fetchall()


def org_id(db_path, name="SIA Ezerkrasta Būve"):
    return q(db_path, "SELECT id FROM organizations WHERE name = ?", name)[0][0]


def request_id(db_path, subject):
    return q(db_path, "SELECT id FROM requests WHERE subject = ?", subject)[0][0]


def user_id(db_path, email):
    return q(db_path, "SELECT id FROM users WHERE email = ?", email)[0][0]


# --- F4 -------------------------------------------------------------------------


def test_add_month():
    assert org_requests.add_month(date(2026, 1, 31)) == date(2026, 2, 28)
    assert org_requests.add_month(date(2026, 12, 15)) == date(2027, 1, 15)


def test_create_request_defaults(client, db_path):
    login(client)
    form_html = client.get(f"/organizacijas/{org_id(db_path)}/pieprasijumi/jauns", headers=HTML).text
    assert f'value="{org_requests.add_month(TODAY).isoformat()}"' in form_html  # noklusētais termiņš
    res = client.post(f"/organizacijas/{org_id(db_path)}/pieprasijumi/jauns",
                      data={"subject": "Telpas semināram", "received": TODAY.isoformat(), "due": ""}, headers=HTML)
    assert res.status_code == 303
    row = q(db_path, "SELECT status, due FROM requests WHERE subject = 'Telpas semināram'")[0]
    assert tuple(row) == ("Jauns", org_requests.add_month(TODAY).isoformat())


@pytest.mark.parametrize("data, message", [
    ({"subject": ""}, "Ievadiet pieprasījuma tematu."),
    ({"received": (TODAY + timedelta(days=1)).isoformat()}, "Saņemšanas datums nevar būt nākotnē."),
    ({"due": (TODAY - timedelta(days=1)).isoformat()}, "Termiņš nevar būt agrāks par saņemšanas datumu."),
])
def test_request_validation(client, db_path, data, message):
    login(client)
    form = {"subject": "Temats", "received": TODAY.isoformat(), "due": "", **data}
    res = client.post(f"/organizacijas/{org_id(db_path)}/pieprasijumi/jauns", data=form, headers=HTML)
    assert res.status_code == 400
    assert message in res.text


# 1: statuss tikai uz priekšu
def test_status_only_forward(client, db_path):
    login(client)
    rid = request_id(db_path, "Atbalsts talkas organizēšanai")  # Jauns, Annas organizācija
    assert client.post(f"/pieprasijumi/{rid}/statuss", data={"status": "Atbildēts"}, headers=HTML).status_code == 400  # nevar izlaist
    assert client.post(f"/pieprasijumi/{rid}/statuss", data={"status": "Darbā"}, headers=HTML).status_code == 303
    assert client.post(f"/pieprasijumi/{rid}/statuss", data={"status": "Jauns"}, headers=HTML).status_code == 400  # atpakaļ nevar
    assert client.post(f"/pieprasijumi/{rid}/statuss", data={"status": "Atbildēts"}, headers=HTML).status_code == 303
    assert q(db_path, "SELECT status FROM requests WHERE id = ?", rid)[0][0] == "Atbildēts"
    assert "Atzīmēt kā atbildētu" not in client.get(f"/pieprasijumi/{rid}", headers=HTML).text


# 2: kavēts tiek aprēķināts
def test_overdue_is_computed_not_stored(client, db_path):
    login(client)
    rid = request_id(db_path, "Būvatļaujas konsultācija krasta zonā")  # termiņš pirms 10 d.
    assert "KAVĒTS (10 d.)" in client.get(f"/pieprasijumi/{rid}", headers=HTML).text
    client.post(f"/pieprasijumi/{rid}/statuss", data={"status": "Atbildēts"}, headers=HTML)
    assert "KAVĒTS" not in client.get(f"/pieprasijumi/{rid}", headers=HTML).text
    columns = [r["name"] for r in q(db_path, "PRAGMA table_info(requests)")]
    assert not any("overdue" in c or "kav" in c for c in columns)


# 3: teksts + ikona ar tekstuālu alternatīvu
def test_overdue_label_has_text_and_icon_alternative(client):
    login(client)
    html = client.get("/pieprasijumi?kaveti=1", headers=HTML).text
    assert re.search(r'<svg class="tag-icon"[^>]*role="img" aria-label="Brīdinājums"', html)
    assert "KAVĒTS (" in html


# 4: filtri
def test_filters(client):
    login(client, "vaditajs@example.com")
    all_html = client.get("/pieprasijumi", headers=HTML).text
    assert "<caption>Pieprasījumi: 12</caption>" in all_html
    overdue = client.get("/pieprasijumi?kaveti=1", headers=HTML).text
    assert "<caption>Pieprasījumi: 4 (filtrēts)</caption>" in overdue  # termiņi -10, -3, -5, -14 d.
    assert "Iedzīvotāju aptaujas rezultāti" not in overdue  # atbildēts, kaut termiņš pagājis
    assert "Pieprasījumi: 1 (filtrēts)" in client.get("/pieprasijumi?statuss=Atbildēts", headers=HTML).text
    jauns = client.get("/pieprasijumi?statuss=Jauns", headers=HTML).text
    assert "Ostas piekļuves saskaņojums" in jauns and "Mācību programmas saskaņošana" not in jauns


def test_employee_edits_only_own_organizations_requests(client, db_path):
    login(client)
    other = request_id(db_path, "Mācību programmas saskaņošana")  # Mārtiņa organizācija
    assert client.post(f"/pieprasijumi/{other}/statuss", data={"status": "Atbildēts"}, headers=HTML).status_code == 403
    assert client.get(f"/organizacijas/{org_id(db_path, 'Nodibinājums Laivu Skola')}/pieprasijumi/jauns", headers=HTML).status_code == 403
    assert client.get(f"/pieprasijumi/{other}", headers=HTML).status_code == 200  # skatīt drīkst


def test_request_changes_logged(client, db_path):
    login(client)
    rid = request_id(db_path, "Atbalsts talkas organizēšanai")
    client.post(f"/pieprasijumi/{rid}/statuss", data={"status": "Darbā"}, headers=HTML)
    assert ("status", "request", rid) in [tuple(r) for r in q(db_path, "SELECT action, object_type, object_id FROM access_log")]


# --- F5 -------------------------------------------------------------------------


# 1: šodien un nokavētie, nokavētie augšā
def test_my_tasks_today(client):
    login(client)
    html = client.get("/uzdevumi", headers=HTML).text
    today_block = html.split('id="sodien"')[1].split('id="nakamie"')[0]
    assert today_block.count('class="task"') == 3
    assert today_block.index("Nokavēts (2 d.)") < today_block.index(">Šodien</span>")
    assert "Saskaņot mācību programmu" not in html  # Mārtiņa uzdevums
    assert "Pārbaudīt granta nolikumu" in html.split('id="nakamie"')[1]  # nākamie


# 2: izpildīts ar vienu POST pogu
def test_complete_task_from_list(client, db_path):
    login(client)
    tid = q(db_path, "SELECT id FROM tasks WHERE description = 'Piezvanīt par talkas datumu'")[0][0]
    res = client.post(f"/uzdevumi/{tid}/izpildits", data={"atpakal": "/uzdevumi"}, headers=HTML)
    assert res.status_code == 303 and res.headers["Location"] == "/uzdevumi"
    assert q(db_path, "SELECT done_at FROM tasks WHERE id = ?", tid)[0][0] is not None
    assert "Piezvanīt par talkas datumu" in client.get("/uzdevumi", headers=HTML).text.split('id="izpilditie"')[1]


def test_redirect_target_is_restricted(client, db_path):
    login(client)
    tid = q(db_path, "SELECT id FROM tasks WHERE description = 'Piezvanīt par talkas datumu'")[0][0]
    res = client.post(f"/uzdevumi/{tid}/izpildits", data={"atpakal": "https://example.org"}, headers=HTML)
    assert res.headers["Location"] == "/panelis"


# 3: vadītājs redz visus, var filtrēt
def test_manager_sees_all_tasks(client, db_path):
    login(client, "vaditajs@example.com")
    html = client.get("/uzdevumi", headers=HTML).text
    assert "Saskaņot mācību programmu" in html and "Piezvanīt par talkas datumu" in html
    martins = user_id(db_path, "darbinieks2@example.com")
    filtered = client.get(f"/uzdevumi?izpilditajs={martins}", headers=HTML).text
    assert "Piezvanīt par talkas datumu" not in filtered and "Saskaņot mācību programmu" in filtered


def test_create_task_for_colleague_appears_in_their_panel(client, db_path):
    login(client)
    martins = user_id(db_path, "darbinieks2@example.com")
    res = client.post("/uzdevumi/jauns", data={"description": "Pārbaudīt līgumu", "assignee_id": str(martins),
                                                "due": TODAY.isoformat(), "organization_id": str(org_id(db_path))}, headers=HTML)
    assert res.status_code == 303
    client.post("/iziet")
    login(client, "darbinieks2@example.com")
    assert "Pārbaudīt līgumu" in client.get("/panelis", headers=HTML).text
    assert "uzdeva Anna Kalniņa" in client.get("/uzdevumi", headers=HTML).text


def test_task_linked_to_request(client, db_path):
    login(client)
    rid = request_id(db_path, "Atbalsts talkas organizēšanai")
    assert "Atbalsts talkas organizēšanai" in client.get(f"/uzdevumi/jauns?pieprasijums={rid}", headers=HTML).text
    res = client.post("/uzdevumi/jauns", data={"description": "Sagatavot atbildi", "assignee_id": str(user_id(db_path, "darbinieks@example.com")),
                                                "due": TODAY.isoformat(), "request_id": str(rid)}, headers=HTML)
    assert res.headers["Location"] == f"/pieprasijumi/{rid}"
    assert "Sagatavot atbildi" in client.get(f"/pieprasijumi/{rid}", headers=HTML).text


@pytest.mark.parametrize("data, message", [
    ({"description": ""}, "Ievadiet, kas jādara."),
    ({"organization_id": ""}, "Uzdevumam jābūt saistītam ar organizāciju vai pieprasījumu."),
    ({"assignee_id": "9999"}, "Izvēlieties izpildītāju."),
    ({"due": ""}, "Ievadiet izpildes datumu."),
])
def test_task_validation(client, db_path, data, message):
    login(client)
    form = {"description": "X", "assignee_id": str(user_id(db_path, "darbinieks@example.com")),
            "due": TODAY.isoformat(), "organization_id": str(org_id(db_path)), **data}
    res = client.post("/uzdevumi/jauns", data=form, headers=HTML)
    assert res.status_code == 400
    assert message in res.text


# --- F9 saites ------------------------------------------------------------------


def test_dashboard_links_to_lists(client):
    login(client)
    html = client.get("/panelis", headers=HTML).text
    assert 'href="/pieprasijumi?statuss=atverti&amp;mani=1"' in html
    assert 'href="/uzdevumi"' in html
    assert re.search(r'href="/pieprasijumi/\d+"', html)
