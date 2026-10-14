"""F0 #7 · pieslēgšanās un reģistrācijas HTML formas bez JavaScript (POST → redirect → GET)."""

import pytest

from app import db, seed
from app.main import create_app

HTML = {"Accept": "text/html"}


@pytest.fixture
def client(tmp_path):
    path = tmp_path / "test.db"
    seed.seed(db.connect(path))
    return create_app(db_path=path).test_client()


def register_form(client, **overrides):
    data = {
        "fullName": "Līga Ozoliņa-Kalniņa",
        "email": "liga@example.com",
        "password": "drosa-parole-123",
        "password2": "drosa-parole-123",
    }
    data.update(overrides)
    return client.post("/register", data=data, headers=HTML)


def test_login_form_redirects_to_panel(client):
    res = client.post("/login", data={"email": "darbinieks@example.com", "password": seed.SEED_PASSWORD}, headers=HTML)
    assert res.status_code == 303
    assert res.headers["Location"] == "/panelis"
    assert "httponly" in res.headers["Set-Cookie"].lower()
    assert "Labdien, Anna!" in client.get("/panelis", headers=HTML).text


def test_login_form_wrong_password_keeps_email(client):
    res = client.post("/login", data={"email": "darbinieks@example.com", "password": "nepareiza-parole"}, headers=HTML)
    assert res.status_code == 401
    assert "Nepareizs e-pasts vai parole." in res.text
    assert 'value="darbinieks@example.com"' in res.text


def test_login_form_empty_fields(client):
    res = client.post("/login", data={"email": "", "password": ""}, headers=HTML)
    assert res.status_code == 400
    assert "Ievadiet e-pastu un paroli." in res.text


def test_logged_in_user_skips_login_page(client):
    client.post("/login", data={"email": "darbinieks@example.com", "password": seed.SEED_PASSWORD}, headers=HTML)
    assert client.get("/login", headers=HTML).headers["Location"] == "/panelis"


def test_register_form_success(client):
    res = register_form(client)
    assert res.status_code == 303
    assert res.headers["Location"] == "/login?registered=1"
    assert "Konts izveidots" in client.get("/login?registered=1", headers=HTML).text


def test_register_form_errors_have_summary_and_field_messages(client):
    res = register_form(client, fullName="J4nis", email="janis@", password="short", password2="short")
    assert res.status_code == 400
    html = res.text
    assert "Lūdzu, izlabojiet 3 kļūdas" in html
    for field in ("fullName", "email", "password"):
        assert f'href="#{field}"' in html  # saite no kopsavilkuma uz lauku
        assert f'id="{field}-error"' in html
    assert 'aria-invalid="true"' in html
    assert "Parolei jābūt vismaz 12 rakstzīmes garai." in html
    assert 'value="janis@"' in html  # ievadītā vērtība saglabājas
    assert "short" not in html.replace("TOO_SHORT", "")  # parole netiek atgriezta lapā


def test_register_form_password_mismatch(client):
    res = register_form(client, password2="cita-parole-456")
    assert res.status_code == 400
    assert "Paroles nesakrīt." in res.text


def test_register_form_duplicate_email(client):
    res = register_form(client, email="Darbinieks@Example.com")
    assert res.status_code == 409
    assert "Šis e-pasts jau ir reģistrēts." in res.text


def test_password_rule_visible_before_input(client):
    html = client.get("/register", headers=HTML).text
    assert "Parolei jābūt vismaz 12 rakstzīmes garai" in html
    assert 'aria-describedby="password-hint"' in html


def test_login_page_has_no_scripts(client):
    assert "<script" not in client.get("/login", headers=HTML).text


def test_browser_404_is_html_page(client):
    res = client.get("/nav-tadas-lapas", headers=HTML)
    assert res.status_code == 404
    assert "Lapa nav atrasta" in res.text


def test_skip_link_on_all_pages(client):
    for path in ("/login", "/register"):
        assert 'href="#saturs"' in client.get(path, headers=HTML).text
