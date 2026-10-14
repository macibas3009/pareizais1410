"""F0 #6 · lietotājs reģistrācijā pieprasa lomu, administrators apstiprina vai noraida."""

import re

import pytest

from app import db, seed
from app.main import create_app

HTML = {"Accept": "text/html"}
PASSWORD = "drosa-parole-123"


@pytest.fixture
def client(tmp_path):
    path = tmp_path / "test.db"
    seed.seed(db.connect(path))
    return create_app(db_path=path).test_client()


def login(client, email, password=seed.SEED_PASSWORD):
    res = client.post("/login", data={"email": email, "password": password}, headers=HTML)
    assert res.status_code == 303, res.text


def register(client, email="jauns@example.com", role="vaditajs"):
    data = {"fullName": "Jauns Lietotājs", "email": email, "requested_role": role, "password": PASSWORD, "password2": PASSWORD}
    return client.post("/register", data=data, headers=HTML)


def pending_id(client):
    login(client, "admin@example.com")
    html = client.get("/panelis", headers=HTML).text
    return re.search(r'action="/lietotaji/(\d+)/loma"', html).group(1), html


def test_registration_requires_role_choice(client):
    data = {"fullName": "Jauns Lietotājs", "email": "jauns@example.com", "password": PASSWORD, "password2": PASSWORD}
    res = client.post("/register", data=data, headers=HTML)
    assert res.status_code == 400
    assert "Izvēlieties, kādu lomu pieprasāt." in res.text


def test_administrator_role_cannot_be_requested(client):
    res = register(client, role="administrators")
    assert res.status_code == 400


def test_pending_user_sees_requested_role(client):
    register(client)
    login(client, "jauns@example.com", PASSWORD)
    html = client.get("/panelis", headers=HTML).text
    assert "Konts gaida apstiprinājumu" in html
    assert "Jūs pieprasījāt lomu: <strong>Vadītājs</strong>" in html


def test_admin_approves_requested_role(client):
    register(client)
    user_id, html = pending_id(client)
    assert "jauns@example.com" in html and "Vadītājs" in html

    res = client.post(f"/lietotaji/{user_id}/loma", data={"role": "vaditajs", "back": "panelis"}, headers=HTML)
    assert res.status_code == 303
    assert "Neviens lietotājs negaida apstiprinājumu." in client.get("/panelis", headers=HTML).text

    client.post("/iziet")
    login(client, "jauns@example.com", PASSWORD)
    assert "organizācijas iestādē" in client.get("/panelis", headers=HTML).text


def test_admin_can_choose_different_role(client):
    register(client, role="vaditajs")
    user_id, _ = pending_id(client)
    client.post(f"/lietotaji/{user_id}/loma", data={"role": "darbinieks"}, headers=HTML)
    assert "Darbinieks" in client.get("/lietotaji", headers=HTML).text


def test_admin_rejects_pending_account(client):
    register(client)
    user_id, _ = pending_id(client)
    assert client.post(f"/lietotaji/{user_id}/noraidit", headers=HTML).status_code == 303
    client.post("/iziet")
    res = client.post("/login", data={"email": "jauns@example.com", "password": PASSWORD}, headers=HTML)
    assert res.status_code == 401  # konts dzēsts


def test_admin_cannot_change_own_role(client):
    login(client, "admin@example.com")
    html = client.get("/lietotaji", headers=HTML).text
    assert "Jūsu konts" in html
    own_id = re.search(r'<tr>\s*<th scope="row">Kārlis Liepa</th>', html)
    assert own_id  # savā rindā nav formas
    conn_rows = re.findall(r'action="/lietotaji/(\d+)/loma"', html)
    assert len(conn_rows) == 3  # 4 sākumdatu lietotāji, izņemot pašu administratoru


def test_only_admin_can_manage_roles(client):
    register(client)
    login(client, "vaditajs@example.com")
    assert client.get("/lietotaji", headers=HTML).status_code == 403
    assert client.post("/lietotaji/1/loma", data={"role": "administrators"}, headers=HTML).status_code == 403


def test_role_changes_are_logged(client):
    register(client)
    user_id, _ = pending_id(client)
    client.post(f"/lietotaji/{user_id}/loma", data={"role": "vaditajs"}, headers=HTML)
    html = client.get("/zurnals", headers=HTML).text
    assert "Apstiprināja lomu" in html
    assert f"Lietotājs #{user_id}" in html
    assert "jauns@example.com" not in html  # žurnālā tikai ID (N2)
