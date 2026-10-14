"""F2 · kontaktpersonas un N2 · glabāšanas termiņš, pārskatīšana, dzēšana pēc pieprasījuma."""

import re
from datetime import date

import pytest

from app import contacts, db, seed
from app.main import create_app

HTML = {"Accept": "text/html"}
VALID = {"full_name": "Ilona Kļaviņa", "position": "Projektu vadītāja", "email": "ilona@example.com",
         "phone": "", "basis_date": "2025-01-15"}


@pytest.fixture
def db_path(tmp_path):
    path = tmp_path / "test.db"
    seed.seed(db.connect(path))
    return path


@pytest.fixture
def client(db_path):
    return create_app(db_path=db_path).test_client()


def login(client, email):
    assert client.post("/login", data={"email": email, "password": seed.SEED_PASSWORD}, headers=HTML).status_code == 303


def q(db_path, sql, *params):
    return db.connect(db_path).execute(sql, params).fetchall()


def org(db_path, name):
    return q(db_path, "SELECT id FROM organizations WHERE name = ?", name)[0][0]


def contact(db_path, name):
    rows = q(db_path, "SELECT id FROM contacts WHERE full_name = ?", name)
    return rows[0][0] if rows else None


def add(client, db_path, org_name="SIA Ezerkrasta Būve", **overrides):
    return client.post(f"/organizacijas/{org(db_path, org_name)}/kontakti/jauns", data={**VALID, **overrides}, headers=HTML)


# --- F2 -------------------------------------------------------------------------


def test_create_contact_with_retention_and_basis(client, db_path):
    login(client, "darbinieks@example.com")
    res = add(client, db_path)
    assert res.status_code == 303
    html = client.get(res.headers["Location"], headers=HTML).text
    assert "Ilona Kļaviņa" in html and "Izmaiņas saglabātas." in html
    row = q(db_path, "SELECT legal_basis, retain_until, phone FROM contacts WHERE full_name = 'Ilona Kļaviņa'")[0]
    assert row["legal_basis"] == "Līgums"
    assert row["retain_until"] == contacts.add_years(date.today(), 3).isoformat()
    assert row["phone"] is None


def test_form_has_only_minimal_fields(client, db_path):
    login(client, "darbinieks@example.com")
    html = client.get(f"/organizacijas/{org(db_path, 'SIA Ezerkrasta Būve')}/kontakti/jauns", headers=HTML).text
    form = html.split('<form method="post" action="/organizacijas/')[1].split("</form>")[0]
    names = set(re.findall(r'<input[^>]* name="([^"]+)"', form))
    assert names == {"full_name", "position", "email", "phone", "basis_date"}  # nav piezīmju lauka (N2 minimizācija)
    assert "<textarea" not in html


@pytest.mark.parametrize("overrides, message", [
    ({"email": "", "phone": ""}, "Norādiet e-pastu vai tālruni (vismaz vienu)."),
    ({"phone": "123"}, "Tālrunim jābūt 8 cipariem"),
    ({"email": "ilona@"}, "Ievadiet derīgu e-pasta adresi"),
    ({"full_name": "1lona"}, "Vārdā drīkst būt tikai burti"),
    ({"basis_date": "2999-01-01"}, "Datums nevar būt nākotnē."),
    ({"position": ""}, "Ievadiet amatu."),
])
def test_validation(client, db_path, overrides, message):
    login(client, "darbinieks@example.com")
    res = add(client, db_path, **overrides)
    assert res.status_code == 400
    assert message in res.text
    assert "Lūdzu, izlabojiet" in res.text


def test_phone_formats_accepted(client, db_path):
    login(client, "darbinieks@example.com")
    assert add(client, db_path, email="", phone="+371 2000 0000").status_code == 303
    assert q(db_path, "SELECT phone FROM contacts WHERE full_name = 'Ilona Kļaviņa'")[0][0] == "+37120000000"


def test_employee_cannot_add_to_others_organization(client, db_path):
    login(client, "darbinieks@example.com")
    assert add(client, db_path, org_name="Nodibinājums Laivu Skola").status_code == 403


def test_contact_card_view_is_logged(client, db_path):
    login(client, "darbinieks@example.com")
    cid = contact(db_path, "Jānis Bērziņš")
    assert "Glabāt līdz" in client.get(f"/kontakti/{cid}", headers=HTML).text
    assert [tuple(r) for r in q(db_path, "SELECT action, object_type, object_id FROM access_log")] == [("view", "contact", cid)]


def test_organization_card_hides_contact_details(client, db_path):
    login(client, "darbinieks@example.com")
    html = client.get(f"/organizacijas/{org(db_path, 'SIA Ezerkrasta Būve')}", headers=HTML).text
    assert "Jānis Bērziņš" in html
    assert "kontakts1@example.com" not in html  # e-pasts tikai kontakta kartītē, kuras atvēršana tiek žurnalēta


def test_edit_own_and_forbid_others(client, db_path):
    login(client, "darbinieks@example.com")
    own = contact(db_path, "Jānis Bērziņš")
    res = client.post(f"/kontakti/{own}/labot", data={**VALID, "full_name": "Jānis Bērziņš", "position": "Direktors"}, headers=HTML)
    assert res.status_code == 303
    assert q(db_path, "SELECT position FROM contacts WHERE id = ?", own)[0][0] == "Direktors"
    other = contact(db_path, "Toms Lazdiņš")  # Mārtiņa organizācija
    assert client.get(f"/kontakti/{other}/labot", headers=HTML).status_code == 403
    assert "/labot" not in client.get(f"/kontakti/{other}", headers=HTML).text.split("Kontaktinformācija")[0]


# --- N2 · "Jāpārskata" ----------------------------------------------------------


def test_review_list_scope(client):
    login(client, "darbinieks@example.com")
    html = client.get("/kontakti/japarskata", headers=HTML).text
    assert html.count('class="review-item"') == 2  # Annas organizāciju kontakti ar beigušos termiņu
    client.post("/iziet")
    login(client, "vaditajs@example.com")
    assert client.get("/kontakti/japarskata", headers=HTML).text.count('class="review-item"') == 3


def test_extend_requires_reason(client, db_path):
    login(client, "darbinieks@example.com")
    cid = contact(db_path, "Līga Ozoliņa")  # termiņš beidzies
    res = client.post(f"/kontakti/{cid}/pagarinat", data={"reason": "  "}, headers=HTML)
    assert res.status_code == 400
    assert "Ievadiet pamatojumu" in res.text


def test_extend_with_reason(client, db_path):
    login(client, "darbinieks@example.com")
    cid = contact(db_path, "Līga Ozoliņa")
    res = client.post(f"/kontakti/{cid}/pagarinat", data={"reason": "Aktīvs līgums līdz 2028. gadam"}, headers=HTML)
    assert res.status_code == 303
    assert q(db_path, "SELECT retain_until FROM contacts WHERE id = ?", cid)[0][0] == contacts.add_years(date.today(), 3).isoformat()
    assert q(db_path, "SELECT reason FROM retention_extensions")[0][0] == "Aktīvs līgums līdz 2028. gadam"
    assert ("extend",) in [tuple(r) for r in q(db_path, "SELECT action FROM access_log")]
    assert "Līga Ozoliņa" not in client.get("/kontakti/japarskata", headers=HTML).text


def test_delete_from_review_only_when_expired(client, db_path):
    login(client, "darbinieks@example.com")
    expired = contact(db_path, "Līga Ozoliņa")
    active = contact(db_path, "Jānis Bērziņš")
    assert client.post(f"/kontakti/{active}/dzest", headers=HTML).status_code == 403
    assert client.get(f"/kontakti/{active}/dzest", headers=HTML).status_code == 403
    confirm = client.get(f"/kontakti/{expired}/dzest", headers=HTML)
    assert "neatgriezeniski" in confirm.text and contact(db_path, "Līga Ozoliņa") is not None  # GET neko nedzēš
    assert client.post(f"/kontakti/{expired}/dzest", headers=HTML).status_code == 303
    assert contact(db_path, "Līga Ozoliņa") is None


# --- N2 · dzēšana pēc pieprasījuma ----------------------------------------------


def request_deletion(client, db_path, name="Jānis Bērziņš"):
    login(client, "darbinieks@example.com")
    cid = contact(db_path, name)
    assert client.post(f"/kontakti/{cid}/dzesanas-pieprasijums", headers=HTML).status_code == 303
    client.post(f"/kontakti/{cid}/dzesanas-pieprasijums", headers=HTML)  # atkārtoti nedublē
    client.post("/iziet")
    return cid


def test_deletion_request_executed_by_admin(client, db_path):
    cid = request_deletion(client, db_path)
    assert len(q(db_path, "SELECT * FROM deletion_requests")) == 1
    login(client, "admin@example.com")
    assert "1</span> <span class=\"stat-label\">dzēšanas pieprasījums gaida" in client.get("/panelis", headers=HTML).text
    rid = q(db_path, "SELECT id FROM deletion_requests")[0][0]
    assert "Jānis Bērziņš" in client.get(f"/dzesanas-pieprasijumi/{rid}/izpildit", headers=HTML).text  # apstiprinājums
    assert contact(db_path, "Jānis Bērziņš") is not None
    assert client.post(f"/dzesanas-pieprasijumi/{rid}/izpildit", headers=HTML).status_code == 303
    assert contact(db_path, "Jānis Bērziņš") is None
    assert q(db_path, "SELECT status FROM deletion_requests")[0][0] == "done"
    html = client.get("/zurnals", headers=HTML).text
    assert f"Kontaktpersona #{cid}" in html and "Dzēsa" in html
    assert "Jānis Bērziņš" not in html  # žurnālā tikai ID


def test_deletion_request_rejected(client, db_path):
    request_deletion(client, db_path)
    login(client, "admin@example.com")
    rid = q(db_path, "SELECT id FROM deletion_requests")[0][0]
    client.post(f"/dzesanas-pieprasijumi/{rid}/noraidit", headers=HTML)
    assert contact(db_path, "Jānis Bērziņš") is not None
    assert q(db_path, "SELECT status FROM deletion_requests")[0][0] == "rejected"


def test_role_boundaries(client):
    login(client, "admin@example.com")
    assert client.get("/kontakti/japarskata", headers=HTML).status_code == 403
    client.post("/iziet")
    login(client, "vaditajs@example.com")
    assert client.get("/dzesanas-pieprasijumi", headers=HTML).status_code == 403


def test_dashboard_review_card_links(client):
    login(client, "darbinieks@example.com")
    assert 'href="/kontakti/japarskata"' in client.get("/panelis", headers=HTML).text
