"""CR-4 · lietotāju reģistrācija un pieslēgšanās. Testa vārdi un e-pasti ir izdomāti."""

import logging
import sqlite3

import pytest

from app.main import create_app

PASSWORD = "drosa-parole-123"


@pytest.fixture
def db_path(tmp_path):
    return tmp_path / "test.db"


@pytest.fixture
def client(db_path):
    return create_app(db_path=db_path, cookie_secure=False).test_client()


def register(client, email="janis@example.com", full_name="Jānis Bērziņš", password=PASSWORD):
    return client.post(
        "/auth/register", json={"email": email, "fullName": full_name, "password": password}
    )


def details(response):
    return [(d["field"], d["issue"]) for d in response.get_json()["error"]["details"]]


# 1
def test_register_returns_user_without_password(client):
    res = register(client, full_name="Līga Ozoliņa-Kalniņa")
    assert res.status_code == 201
    body = res.get_json()
    assert set(body) == {"id", "email", "fullName"}
    assert body["fullName"] == "Līga Ozoliņa-Kalniņa"


# 2
def test_register_duplicate_email_case_insensitive(client):
    assert register(client).status_code == 201
    res = register(client, email="  Janis@Example.COM ")
    assert res.status_code == 409
    assert res.get_json()["error"]["code"] == "EMAIL_TAKEN"


# 3
def test_register_invalid_email(client):
    res = register(client, email="janis@")
    assert res.status_code == 400
    assert res.get_json()["error"]["code"] == "VALIDATION_ERROR"
    assert ("email", "INVALID_FORMAT") in details(res)


def test_register_invalid_full_name(client):
    res = register(client, full_name="J4nis")
    assert res.status_code == 400
    assert ("fullName", "INVALID_FORMAT") in details(res)


# 4
def test_register_short_password(client):
    res = register(client, password="short")
    assert res.status_code == 400
    assert ("password", "TOO_SHORT") in details(res)


def test_register_missing_field(client):
    res = client.post("/auth/register", json={"email": "janis@example.com"})
    assert res.status_code == 400
    assert ("fullName", "REQUIRED") in details(res)
    assert ("password", "REQUIRED") in details(res)


# 5, 7
def test_login_sets_httponly_cookie_and_me_works(client):
    register(client)
    res = client.post("/auth/login", json={"email": "JANIS@example.com", "password": PASSWORD})
    assert res.status_code == 200
    assert "httponly" in res.headers["Set-Cookie"].lower()

    me = client.get("/auth/me")
    assert me.status_code == 200
    assert me.get_json()["email"] == "janis@example.com"


# 6
def test_wrong_password_and_unknown_email_look_the_same(client):
    register(client)
    wrong = client.post("/auth/login", json={"email": "janis@example.com", "password": "nepareiza-parole"})
    unknown = client.post("/auth/login", json={"email": "nav@example.com", "password": PASSWORD})
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.get_json() == unknown.get_json()
    assert wrong.get_json()["error"]["code"] == "INVALID_CREDENTIALS"


# 7
def test_me_without_session(client):
    res = client.get("/auth/me")
    assert res.status_code == 401
    assert res.get_json()["error"]["code"] == "UNAUTHENTICATED"


# 8
def test_logout_invalidates_session(client):
    register(client)
    client.post("/auth/login", json={"email": "janis@example.com", "password": PASSWORD})
    token = client.get_cookie("session").value

    assert client.post("/auth/logout").status_code == 204
    client.set_cookie("session", token)  # vecais marķieris vairs nedrīkst darboties
    assert client.get("/auth/me").status_code == 401


# 9
def test_password_stored_only_as_hash(client, db_path):
    register(client)
    conn = sqlite3.connect(db_path)
    (stored,) = conn.execute("SELECT password_hash FROM users").fetchone()
    assert PASSWORD not in stored
    assert stored.startswith("scrypt$")


def test_users_survive_restart(db_path):
    register(create_app(db_path=db_path).test_client())
    fresh = create_app(db_path=db_path).test_client()
    res = fresh.post("/auth/login", json={"email": "janis@example.com", "password": PASSWORD})
    assert res.status_code == 200


# 10
def test_logs_contain_no_personal_data(client, caplog):
    caplog.set_level(logging.DEBUG)
    register(client)
    client.post("/auth/login", json={"email": "janis@example.com", "password": "nepareiza-parole"})
    client.post("/auth/login", json={"email": "janis@example.com", "password": PASSWORD})
    for secret in ("janis@example.com", "Jānis", PASSWORD, "nepareiza-parole"):
        assert secret not in caplog.text


# 11
@pytest.mark.parametrize("path", ["/login", "/register"])
def test_pages_are_served(client, path):
    res = client.get(path)
    assert res.status_code == 200
    assert "<form" in res.text


def test_unknown_path_uses_error_schema(client):
    res = client.get("/nav-tadas-lapas")
    assert res.status_code == 404
    assert res.get_json()["error"]["code"] == "NOT_FOUND"
