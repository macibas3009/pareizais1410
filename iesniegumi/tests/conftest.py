"""Testu kopīgie palīgi. app.py tiek ielādēts pēc faila ceļa ar unikālu nosaukumu,
lai tas nesajauktos ar repozitorija CRM pakotni `app`."""

import importlib.util
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parents[1]
if str(HERE) not in sys.path:
    sys.path.append(str(HERE))  # seed.py, views.py, ai.py

_spec = importlib.util.spec_from_file_location("iesniegumi_app", HERE / "app.py")
iesniegumi_app = importlib.util.module_from_spec(_spec)
sys.modules["iesniegumi_app"] = iesniegumi_app
_spec.loader.exec_module(iesniegumi_app)

HTML = {"Accept": "text/html"}


@pytest.fixture
def app(tmp_path):
    return iesniegumi_app.create_app(tmp_path / "test.db")


@pytest.fixture
def client(app):
    return app.test_client()


def as_role(client, loma):
    res = client.post("/loma", data={"loma": loma})
    assert res.status_code == 303
    return client


@pytest.fixture
def darbinieks(client):
    return as_role(client, "darbinieks")


@pytest.fixture
def vaditajs(client):
    return as_role(client, "vaditajs")


def q(app, sql, *params):
    import sqlite3
    conn = sqlite3.connect(app.config["DB_PATH"])
    conn.row_factory = sqlite3.Row
    try:
        return conn.execute(sql, params).fetchall()
    finally:
        conn.close()
