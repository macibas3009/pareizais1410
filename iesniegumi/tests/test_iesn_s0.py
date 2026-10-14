"""S0 · iesildīšanās: sākumlapa, testa dati, lomas izvēle."""

from conftest import as_role, q


def test_start_page_offers_three_roles(client):
    html = client.get("/").text
    assert '<html lang="lv">' in html
    for role in ("Iedzīvotājs", "Darbinieks", "Vadītājs"):
        assert f"<strong>{role}</strong>" in html
    assert 'href="#saturs"' in html  # skip-link


def test_seed_has_10_submissions_in_5_topics(app):
    assert q(app, "SELECT COUNT(*) FROM iesniegumi")[0][0] == 10
    assert q(app, "SELECT COUNT(DISTINCT tema_id) FROM iesniegumi")[0][0] == 5
    assert q(app, "SELECT numurs FROM iesniegumi ORDER BY id LIMIT 1")[0][0].endswith("-0001")


def test_role_choice_redirects(client):
    res = client.post("/loma", data={"loma": "darbinieks"})
    assert res.headers["Location"].endswith("/darbinieks/iesniegumi")
    assert client.post("/loma", data={"loma": "hakeris"}).status_code == 400


def test_unknown_page_404(client):
    res = client.get("/nav")
    assert res.status_code == 404 and "Lapa nav atrasta" in res.text
