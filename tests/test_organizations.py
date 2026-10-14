"""F1 · organizācijas: saraksts, kartīte, izveide, labošana, tiesības un piekļuves žurnāls."""

import re

import pytest

from app import db, seed
from app.main import create_app

HTML = {"Accept": "text/html"}


@pytest.fixture
def db_path(tmp_path):
    path = tmp_path / "test.db"
    seed.seed(db.connect(path))
    return path


@pytest.fixture
def client(db_path):
    return create_app(db_path=db_path).test_client()


def login(client, email):
    res = client.post("/login", data={"email": email, "password": seed.SEED_PASSWORD}, headers=HTML)
    assert res.status_code == 303


def org_id(db_path, name):
    return db.connect(db_path).execute("SELECT id FROM organizations WHERE name = ?", (name,)).fetchone()[0]


VALID = {"name": "SIA Jauna Laiva", "reg_no": "40003999999", "kind": "Uzņēmums"}


# 1: saraksts ir tabula ar caption un th scope; filtri
def test_list_is_accessible_table_with_filters(client):
    login(client, "darbinieks@example.com")
    html = client.get("/organizacijas", headers=HTML).text
    assert "<caption>Organizācijas: 10</caption>" in html
    assert 'scope="col"' in html and 'scope="row"' in html
    assert "<caption>Organizācijas: 3 (filtrēts)</caption>" in client.get("/organizacijas?veids=NVO&atbildigais=", headers=HTML).text
    mine = client.get("/organizacijas?atbildigais=mani", headers=HTML).text
    assert "Organizācijas: 4 (filtrēts)" in mine
    assert "Nodibinājums Laivu Skola" not in mine


# 2: forma ar label un kļūdām; vērtības saglabājas
def test_create_validation_errors(client):
    login(client, "darbinieks@example.com")
    res = client.post("/organizacijas/jauna", data={"name": "X", "reg_no": "123", "kind": ""}, headers=HTML)
    assert res.status_code == 400
    html = res.text
    assert "Lūdzu, izlabojiet 3 kļūdas" in html
    assert "Reģistrācijas numuram jābūt 11 cipariem" in html
    assert 'value="123"' in html
    assert '<label for="reg_no">' in html


# 3: dublēts reģ. nr.
def test_duplicate_reg_no(client):
    login(client, "darbinieks@example.com")
    res = client.post("/organizacijas/jauna", data={**VALID, "reg_no": "40003000001"}, headers=HTML)
    assert res.status_code == 400
    assert "Organizācija ar šo reģ. nr. jau ir reģistrēta." in res.text


def test_employee_creates_and_becomes_responsible(client, db_path):
    login(client, "darbinieks@example.com")
    res = client.post("/organizacijas/jauna", data={**VALID, "responsible_id": "999"}, headers=HTML)
    assert res.status_code == 303
    html = client.get(res.headers["Location"], headers=HTML).text
    assert "SIA Jauna Laiva" in html and "Izmaiņas saglabātas." in html
    row = db.connect(db_path).execute(
        "SELECT u.email FROM organizations o JOIN users u ON u.id = o.responsible_id WHERE o.reg_no = ?", (VALID["reg_no"],)
    ).fetchone()
    assert row["email"] == "darbinieks@example.com"  # darbinieks nevar norādīt citu atbildīgo


def test_manager_chooses_responsible(client, db_path):
    login(client, "vaditajs@example.com")
    martins = db.connect(db_path).execute("SELECT id FROM users WHERE email = 'darbinieks2@example.com'").fetchone()[0]
    res = client.post("/organizacijas/jauna", data={**VALID, "responsible_id": str(martins)}, headers=HTML)
    assert res.status_code == 303
    assert "Mārtiņš Ozols" in client.get(res.headers["Location"], headers=HTML).text


# 4: kartīte ar pamatdatiem, kontaktiem, hronoloģiju, pieprasījumiem, uzdevumiem
def test_card_contents(client, db_path):
    login(client, "darbinieks@example.com")
    html = client.get(f"/organizacijas/{org_id(db_path, 'SIA Ezerkrasta Būve')}", headers=HTML).text
    for heading in ("Pamatdati", "Kontaktpersonas (2)", "Pieprasījumi", "Uzdevumi", "Mijiedarbību hronoloģija (3)"):
        assert heading in html
    dates = re.findall(r"(\d\d)\.(\d\d)\.(\d{4}) · (?:Zvans|E-pasts|Sanāksme)", html)
    as_iso = [f"{y}-{m}-{d}" for d, m, y in dates]
    assert as_iso == sorted(as_iso, reverse=True)  # jaunākā augšā


# 5: kartītes atvēršana tiek ierakstīta žurnālā
def test_card_view_is_logged(client, db_path):
    login(client, "darbinieks@example.com")
    oid = org_id(db_path, "SIA Ezerkrasta Būve")
    client.get(f"/organizacijas/{oid}", headers=HTML)
    rows = db.connect(db_path).execute("SELECT action, object_type, object_id FROM access_log").fetchall()
    assert [tuple(r) for r in rows] == [("view", "organization", oid)]


# 6: darbinieks nelabo citu organizācijas
def test_employee_cannot_edit_others(client, db_path):
    login(client, "darbinieks@example.com")
    other = org_id(db_path, "Nodibinājums Laivu Skola")
    html = client.get(f"/organizacijas/{other}", headers=HTML).text
    assert f"/organizacijas/{other}/labot" not in html
    assert client.get(f"/organizacijas/{other}/labot", headers=HTML).status_code == 403
    assert client.post(f"/organizacijas/{other}/labot", data=VALID, headers=HTML).status_code == 403


def test_employee_edits_own(client, db_path):
    login(client, "darbinieks@example.com")
    own = org_id(db_path, "SIA Ezerkrasta Būve")
    res = client.post(f"/organizacijas/{own}/labot", data={"name": "SIA Ezerkrasta Būve un Ko", "reg_no": "40003000001", "kind": "Uzņēmums"}, headers=HTML)
    assert res.status_code == 303
    assert "SIA Ezerkrasta Būve un Ko" in client.get(f"/organizacijas/{own}", headers=HTML).text
    actions = [r[0] for r in db.connect(db_path).execute("SELECT action FROM access_log")]
    assert "update" in actions


def test_manager_edits_any(client, db_path):
    login(client, "vaditajs@example.com")
    other = org_id(db_path, "Nodibinājums Laivu Skola")
    assert client.get(f"/organizacijas/{other}/labot", headers=HTML).status_code == 200


def test_admin_and_anonymous_have_no_access(client):
    assert client.get("/organizacijas", headers=HTML).headers["Location"] == "/login"
    login(client, "admin@example.com")
    assert client.get("/organizacijas", headers=HTML).status_code == 403


def test_unknown_organization_404(client):
    login(client, "darbinieks@example.com")
    assert client.get("/organizacijas/9999", headers=HTML).status_code == 404


def test_dashboard_card_links_to_own_organizations(client):
    login(client, "darbinieks@example.com")
    assert 'href="/organizacijas?atbildigais=mani"' in client.get("/panelis", headers=HTML).text
