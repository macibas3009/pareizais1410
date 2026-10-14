"""F6 · meklēšana un F7 · pārskats vadītājam."""

import re
from datetime import date, timedelta

import pytest

from app import db, report, seed
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


def login(client, email="darbinieks@example.com"):
    assert client.post("/login", data={"email": email, "password": seed.SEED_PASSWORD}, headers=HTML).status_code == 303


def q(db_path, sql, *params):
    return db.connect(db_path).execute(sql, params).fetchall()


# --- F6 -------------------------------------------------------------------------


def test_search_field_in_header_on_all_pages(client):
    login(client)
    for path in ("/panelis", "/organizacijas", "/uzdevumi"):
        html = client.get(path, headers=HTML).text
        assert 'role="search"' in html and '<label for="q"' in html


def test_search_across_types(client):
    login(client)
    html = client.get("/meklet?q=talk", headers=HTML).text  # pieprasījums "Atbalsts talkas organizēšanai"
    assert "Atbalsts talkas organizēšanai" in html
    html = client.get("/meklet?q=ezer", headers=HTML).text
    assert "<caption>Organizācijas: 3</caption>" in html
    assert "Meklēšanas rezultāti: 3 atrasti" in html
    html = client.get("/meklet?q=bērziņš", headers=HTML).text  # kontaktpersona, mazie burti ar garumzīmēm
    assert "Jānis Bērziņš" in html and "<caption>Kontaktpersonas: 1</caption>" in html


def test_search_case_insensitive_for_latvian_letters(client):
    login(client)
    assert "Līga Ozoliņa" in client.get("/meklet?q=LĪGA", headers=HTML).text


def test_diacritics_must_be_entered(client):
    login(client)
    assert "Līga Ozoliņa" not in client.get("/meklet?q=liga", headers=HTML).text


def test_search_by_reg_no_and_email(client):
    login(client)
    assert "SIA Ezerkrasta Būve" in client.get("/meklet?q=40003000001", headers=HTML).text
    html = client.get("/meklet?q=kontakts1@", headers=HTML).text
    assert "Jānis Bērziņš" in html
    assert "kontakts1@example.com" not in html.split("<main")[1]  # rezultātos e-pasts netiek rādīts


def test_interaction_text_not_searched(client):
    login(client)
    html = client.get("/meklet?q=krasta joslas", headers=HTML).text  # vārdi tikai mijiedarbību kopsavilkumā
    assert "Meklēšanas rezultāti: 0 atrasti" in html


def test_minimum_length(client):
    login(client)
    html = client.get("/meklet?q=a", headers=HTML).text
    assert "Vaicājums ir par īsu" in html


def test_like_wildcards_are_literal(client):
    login(client)
    assert "Meklēšanas rezultāti: 0 atrasti" in client.get("/meklet?q=%25%25", headers=HTML).text


def test_contact_open_from_results_is_logged(client, db_path):
    login(client)
    html = client.get("/meklet?q=bērziņš", headers=HTML).text
    href = re.search(r'href="(/kontakti/\d+)"', html).group(1)
    client.get(href, headers=HTML)
    assert ("view", "contact") in [tuple(r) for r in q(db_path, "SELECT action, object_type FROM access_log")]


def test_admin_cannot_search_crm(client):
    login(client, "admin@example.com")
    assert client.get("/meklet?q=ezer", headers=HTML).status_code == 403
    assert 'role="search"' not in client.get("/panelis", headers=HTML).text


# --- F7 -------------------------------------------------------------------------


def test_report_only_for_manager(client):
    login(client)
    assert client.get("/parskats", headers=HTML).status_code == 403
    assert "/parskats" not in client.get("/panelis", headers=HTML).text


def test_report_contents(client):
    login(client, "vaditajs@example.com")
    html = client.get("/parskats", headers=HTML).text
    assert "Aktivitāte pa darbiniekiem" in html and "Aktīvākās organizācijas" in html and "Kavētie pieprasījumi (4)" in html
    # diagramma ar teksta aprakstu un tā pati informācija tabulā
    assert re.search(r'<svg[^>]*role="img" aria-labelledby="chart-title chart-desc"', html)
    assert "<figcaption>" in html
    desc = re.search(r"<desc[^>]*>(.*?)</desc>", html, re.S).group(1)
    table = html.split("Aktivitāte pa darbiniekiem (tie paši dati)")[1].split("</table>")[0]
    for name, n in re.findall(r"(\w[\wāčēģīķļņšūž ]+): (\d+)\.", desc):
        assert re.search(rf'<th scope="row">{name.strip()}</th><td class="num">{n}</td>', table)
    assert html.count('<tr><td>') <= report.TOP_N


def test_report_period(client):
    login(client, "vaditajs@example.com")
    week = client.get("/parskats?periods=7", headers=HTML).text
    quarter = client.get("/parskats?periods=90", headers=HTML).text
    total = lambda h: int(re.search(r'stat-value">(\d+)</span> <span class="stat-label">mijiedarbīb', h).group(1))  # noqa: E731
    assert total(week) == 4 and total(quarter) == 30  # sākumdati: ik pa 2 dienām, pēdējās 60 dienas
    assert 'value="7" selected' in week
    assert 'value="30" selected' in client.get("/parskats?periods=999", headers=HTML).text  # nederīgs → noklusējums


def test_manager_dashboard_links_to_report(client):
    login(client, "vaditajs@example.com")
    assert 'href="/parskats"' in client.get("/panelis", headers=HTML).text


def test_nice_step():
    assert [report.nice_step(v) for v in (0, 4, 8, 23, 140)] == [1, 1, 2, 5, 50]


def test_bar_geometry_scales_to_axis():
    rows = [{"full_name": "A", "n": 8}, {"full_name": "B", "n": 0}]
    chart = report.bar_chart(rows)
    plot_w = chart["width"] - chart["label_w"] - chart["value_w"]
    assert chart["bars"][0]["w"] == pytest.approx(plot_w)
    assert chart["bars"][1]["path"] == ""  # nulles vērtībai nav stabiņa, tikai skaitlis
    assert chart["ticks"][-1]["value"] == 8
