"""US-1 iesniegšana, US-2 apstiprinājums, US-8 mans iesniegums."""

import re

from conftest import HTML, q

VALID = {"vards": "Anna Testere", "epasts": "anna@example.com", "tema": "1", "vieta": "Ezera iela 5",
         "apraksts": "Pie mājas ir liela bedre.", "piekrisana": "1"}


def submit(client, **overrides):
    return client.post("/iesniegt", data={**VALID, **overrides}, headers=HTML)


# --- US-1 ----------------------------------------------------------------------------


def test_form_fields_have_labels_and_required_text(client):
    html = client.get("/iesniegt").text
    for field in ("vards", "epasts", "tema", "vieta", "apraksts", "piekrisana"):
        assert f'<label for="{field}">' in html, field
    assert html.count("(obligāts)") == 6  # 1.4.1: obligātums tekstā, ne tikai krāsā
    options = re.findall(r'<option value="(\d+)">', html)
    assert len(options) == 6  # tēmas no DB


def test_empty_form_shows_summary_and_field_errors(client):
    res = client.post("/iesniegt", data={}, headers=HTML)
    assert res.status_code == 400
    html = res.text
    assert 'id="kludas"' in html and 'role="alert"' in html and 'tabindex="-1"' in html
    assert "Formā ir 6 kļūdas" in html
    for field in ("vards", "epasts", "tema", "vieta", "apraksts", "piekrisana"):
        assert f'href="#{field}"' in html
        assert f'id="{field}-kluda"' in html
        assert re.search(rf'id="{field}"[^>]*aria-describedby="[^"]*{field}-kluda"', html), field
    assert 'document.getElementById("kludas").focus()' in html
    assert html.startswith("<!doctype html>") and "<title>Kļūda: Iesniegt iesniegumu" in html


def test_errors_say_how_to_fix_and_keep_values(client):
    res = submit(client, epasts="anna@", apraksts="")
    html = res.text
    assert "Ievadiet e-pastu formā vards@domens.lv." in html
    assert 'value="anna@"' in html and 'value="Anna Testere"' in html and 'value="Ezera iela 5"' in html
    assert re.search(r'<option value="1" selected>', html)
    assert 'id="piekrisana" name="piekrisana" value="1" required checked' in html


def test_name_and_length_validation(client):
    assert "Vārdā drīkst būt tikai burti" in submit(client, vards="Anna 123").text
    assert "Apraksts ir par garu" in submit(client, apraksts="x" * 3001).text
    assert "Izvēlieties tēmu no saraksta" in submit(client, tema="99").text


def test_successful_submission_creates_number_and_event(app, client):
    res = submit(client)
    assert res.status_code == 303
    numurs = res.headers["Location"].rsplit("/", 1)[1]
    assert re.fullmatch(r"\d{4}-0011", numurs)  # 10 testa iesniegumi + 1
    row = q(app, "SELECT statuss, piekrisana FROM iesniegumi WHERE numurs = ?", numurs)[0]
    assert tuple(row) == ("Jauns", 1)
    assert q(app, "SELECT veids FROM notikumi n JOIN iesniegumi i ON i.id = n.iesniegums_id WHERE numurs = ?", numurs)[0][0] == "iesniegts"


def test_no_time_limit_on_form(client):
    html = client.get("/iesniegt").text
    assert "http-equiv=\"refresh\"" not in html and "Laika ierobežojuma nav" in html


# --- US-2 ----------------------------------------------------------------------------


def test_confirmation_page(client):
    numurs = submit(client).headers["Location"].rsplit("/", 1)[1]
    html = client.get(f"/iesniegts/{numurs}").text
    assert f"<title>Iesniegums reģistrēts: {numurs}" in html  # 2.4.2
    assert f"<strong>{numurs}</strong>" in html                  # 1.1.1 numurs tekstā
    assert "Kas notiks tālāk" in html
    assert f'href="/mans-iesniegums?numurs={numurs}"' in html   # 3.3.7 numurs nav jāpārraksta


def test_refresh_does_not_duplicate(app, client):
    location = submit(client).headers["Location"]
    for _ in range(3):
        client.get(location)  # F5 uz apstiprinājuma lapas
    assert q(app, "SELECT COUNT(*) FROM iesniegumi")[0][0] == 11


def test_unknown_confirmation_404(client):
    assert client.get("/iesniegts/2099-0001").status_code == 404


# --- US-8 ----------------------------------------------------------------------------


def test_status_lookup_shows_status_without_personal_data(app, client):
    numurs, vards, epasts = q(app, "SELECT numurs, vards, epasts FROM iesniegumi WHERE statuss = 'Atbildēts' LIMIT 1")[0]
    html = client.get(f"/mans-iesniegums?numurs={numurs}").text
    assert "Atbildēts" in html and "Atbilde" in html and "Pēdējais notikums" in html
    assert vards not in html and epasts not in html  # VDAR: nerāda iesniedzēja datus


def test_status_lookup_not_found_in_text(client):
    res = client.get("/mans-iesniegums?numurs=2099-9999")
    assert res.status_code == 404
    assert "Iesniegums ar numuru 2099-9999 nav atrasts" in res.text
    assert 'aria-invalid="true"' in res.text and 'aria-describedby="numurs-hint numurs-kluda"' in res.text


def test_status_lookup_bad_format(client):
    assert "nav pareizā formā" in client.get("/mans-iesniegums?numurs=abc").text


def test_no_captcha(client):
    html = client.get("/mans-iesniegums").text.lower()
    assert "captcha" not in html and "recaptcha" not in html
    assert html.count("<input") == 1  # viens lauks
