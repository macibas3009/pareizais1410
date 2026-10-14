"""N3 · lomu tiesību matrica (prasību saraksts, 3. nodaļa) un F8 · piekļūstamības paziņojums."""

import pytest

from app import db, seed
from app.main import create_app

HTML = {"Accept": "text/html"}
PENDING = "gaida@example.com"
PASSWORD = "drosa-parole-123"

# lapa → sagaidāmais statuss katrai lomai: anonīms, bez lomas, darbinieks, vadītājs, administrators
OK, LOGIN, DENY = 200, 303, 403
MATRIX = {
    "/panelis":               (LOGIN, OK, OK, OK, OK),
    "/organizacijas":         (LOGIN, DENY, OK, OK, DENY),
    "/organizacijas/jauna":   (LOGIN, DENY, OK, OK, DENY),
    "/pieprasijumi":          (LOGIN, DENY, OK, OK, DENY),
    "/uzdevumi":              (LOGIN, DENY, OK, OK, DENY),
    "/uzdevumi/jauns":        (LOGIN, DENY, OK, OK, DENY),
    "/kontakti/japarskata":   (LOGIN, DENY, OK, OK, DENY),
    "/meklet?q=ezer":         (LOGIN, DENY, OK, OK, DENY),
    "/parskats":              (LOGIN, DENY, DENY, OK, DENY),
    "/lietotaji":             (LOGIN, DENY, DENY, DENY, OK),
    "/dzesanas-pieprasijumi": (LOGIN, DENY, DENY, DENY, OK),
    "/zurnals":               (LOGIN, DENY, DENY, DENY, OK),
    "/pieklustamiba":         (OK, OK, OK, OK, OK),
}
ROLES = ["anonīms", "bez lomas", "darbinieks", "vadītājs", "administrators"]
EMAILS = {"bez lomas": PENDING, "darbinieks": "darbinieks@example.com",
          "vadītājs": "vaditajs@example.com", "administrators": "admin@example.com"}


@pytest.fixture(scope="module")
def app(tmp_path_factory):
    path = tmp_path_factory.mktemp("matrix") / "test.db"
    seed.seed(db.connect(path))
    application = create_app(db_path=path)
    application.test_client().post("/register", data={
        "fullName": "Gaida Lomu", "email": PENDING, "requested_role": "darbinieks", "password": PASSWORD, "password2": PASSWORD,
    }, headers=HTML)
    return application


def client_for(app, role):
    client = app.test_client()
    if role != "anonīms":
        password = PASSWORD if role == "bez lomas" else seed.SEED_PASSWORD
        assert client.post("/login", data={"email": EMAILS[role], "password": password}, headers=HTML).status_code == 303
    return client


@pytest.mark.parametrize("role", ROLES)
def test_role_matrix(app, role):
    client = client_for(app, role)
    column = ROLES.index(role)
    wrong = {path: client.get(path, headers=HTML).status_code for path in MATRIX}
    wrong = {path: (got, MATRIX[path][column]) for path, got in wrong.items() if got != MATRIX[path][column]}
    assert not wrong, f"{role}: {wrong}"


def test_employee_edit_rights_on_own_vs_other(app):
    """Darbinieks labo savas organizācijas, vadītājs visas (3. nodaļa)."""
    employee, manager = client_for(app, "darbinieks"), client_for(app, "vadītājs")
    own, other = 1, 5  # sākumdati: 1 = SIA Ezerkrasta Būve (Anna), 5 = Nodibinājums Laivu Skola (Mārtiņš)
    assert employee.get(f"/organizacijas/{own}/labot", headers=HTML).status_code == OK
    assert employee.get(f"/organizacijas/{other}/labot", headers=HTML).status_code == DENY
    assert employee.get(f"/organizacijas/{other}/kontakti/jauns", headers=HTML).status_code == DENY
    assert employee.get(f"/organizacijas/{other}/pieprasijumi/jauns", headers=HTML).status_code == DENY
    assert employee.get(f"/organizacijas/{other}/mijiedarbibas/jauna", headers=HTML).status_code == OK  # mijiedarbību drīkst jebkurai
    for path in (f"/organizacijas/{other}/labot", f"/organizacijas/{other}/kontakti/jauns", f"/organizacijas/{other}/pieprasijumi/jauns"):
        assert manager.get(path, headers=HTML).status_code == OK


# --- F8 -------------------------------------------------------------------------


def test_statement_link_in_footer_everywhere(app):
    anon, employee = client_for(app, "anonīms"), client_for(app, "darbinieks")
    for client, path in ((anon, "/login"), (anon, "/register"), (employee, "/panelis"), (employee, "/organizacijas")):
        assert 'href="/pieklustamiba"' in client.get(path, headers=HTML).text, path


def test_statement_contents(app):
    html = client_for(app, "anonīms").get("/pieklustamiba", headers=HTML).text
    for part in ("Atbilstības statuss", "EN 301 549", "WCAG 2.2 AA", "Testu atradumi", "Zināmie ierobežojumi",
                 "Atsauksmes un kontakti", "Ekrāna lasītājs NVDA", "Nav veikts"):
        assert part in html, part
    assert "Pēdējā automātiskā pārbaude" in html  # docs/a11y-rezultati.json no make a11y
    assert "<caption>Rezultāti pa lapām</caption>" in html
