"""F3 · mijiedarbības, MI-1 · kopsavilkums, kā arī F2/N2 daļas, kas atkarīgas no mijiedarbībām."""

import re
from datetime import date, timedelta

import pytest

from app import ai, contacts, db, seed
from app.main import create_app

HTML = {"Accept": "text/html"}
NOTES = (
    "Tikāmies ar biedrības valdi par pavasara talku. Vienojāmies, ka talka notiks maijā Ezera krastā. "
    "Biedrība lūdz pašvaldības atbalstu ar atkritumu maisiem. Laikapstākļi bija jauki. "
    "Jānosūta atbalsta pieteikuma veidlapa līdz piektdienai."
)


@pytest.fixture(autouse=True)
def no_api_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)


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


def org_id(db_path, name="SIA Ezerkrasta Būve"):
    return q(db_path, "SELECT id FROM organizations WHERE name = ?", name)[0][0]


def contact_id(db_path, name):
    return q(db_path, "SELECT id FROM contacts WHERE full_name = ?", name)[0][0]


def user_id(db_path, email):
    return q(db_path, "SELECT id FROM users WHERE email = ?", email)[0][0]


def save(client, oid, **data):
    form = {"action": "save", "kind": "Sanāksme", "date": date.today().isoformat(), "summary": "Apspriesta talka.", **data}
    return client.post(f"/organizacijas/{oid}/mijiedarbibas/jauna", data=form, headers=HTML)


# --- F3 -------------------------------------------------------------------------


def test_create_interaction_appears_first_on_card(client, db_path):
    login(client)
    oid = org_id(db_path)
    res = save(client, oid, contacts=str(contact_id(db_path, "Jānis Bērziņš")), staff=str(user_id(db_path, "darbinieks@example.com")),
               summary="Vienojāmies par talku maijā.", next_step="Nosūtīt veidlapu")
    assert res.status_code == 303
    html = client.get(res.headers["Location"], headers=HTML).text
    assert "Mijiedarbība saglabāta." in html
    timeline = html.split('class="timeline"')[1]
    assert timeline.index("Vienojāmies par talku maijā.") < timeline.index("Apspriests kopīgs")  # jaunākā augšā
    assert "Dalībnieki: Jānis Bērziņš, Anna Kalniņa" in html
    assert ("create", "interaction") in [tuple(r) for r in q(db_path, "SELECT action, object_type FROM access_log")]


@pytest.mark.parametrize("data, message", [
    ({"kind": ""}, "Izvēlieties mijiedarbības veidu."),
    ({"date": (date.today() + timedelta(days=1)).isoformat()}, "Datums nevar būt nākotnē."),
    ({"summary": ""}, "Ievadiet kopsavilkumu vai izveidojiet to ar MI."),
    ({}, "Atzīmējiet vismaz vienu dalībnieku."),
])
def test_validation(client, db_path, data, message):
    login(client)
    res = save(client, org_id(db_path), **data)
    assert res.status_code == 400
    assert message in res.text


def test_participant_from_other_organization_is_ignored(client, db_path):
    login(client)
    foreign = contact_id(db_path, "Toms Lazdiņš")  # cita organizācija
    res = save(client, org_id(db_path), contacts=str(foreign))
    assert res.status_code == 400
    assert "Atzīmējiet vismaz vienu dalībnieku." in res.text


def test_any_employee_can_add_to_any_organization(client, db_path):
    login(client)
    other = org_id(db_path, "Nodibinājums Laivu Skola")
    assert save(client, other, staff=str(user_id(db_path, "darbinieks@example.com"))).status_code == 303


def test_admin_cannot_add(client, db_path):
    login(client, "admin@example.com")
    assert client.get(f"/organizacijas/{org_id(db_path)}/mijiedarbibas/jauna", headers=HTML).status_code == 403


# --- F2 #2: glabāšanas termiņš pārrēķināts pēc mijiedarbības ---------------------


def test_retention_recalculated_from_interaction_date(client, db_path):
    login(client)
    cid = contact_id(db_path, "Līga Ozoliņa")  # termiņš beidzies
    past = date.today() - timedelta(days=10)
    save(client, org_id(db_path), contacts=str(cid), date=past.isoformat())
    assert q(db_path, "SELECT retain_until FROM contacts WHERE id = ?", cid)[0][0] == contacts.add_years(past, 3).isoformat()
    assert "Līga Ozoliņa" not in client.get("/kontakti/japarskata", headers=HTML).text


# --- N2 #5: dzēsta kontaktpersona mijiedarbībās ----------------------------------


def test_deleted_contact_shown_anonymously(client, db_path):
    login(client)
    oid = org_id(db_path)
    cid = contact_id(db_path, "Jānis Bērziņš")  # seed: dalībnieks Annas organizācijas mijiedarbībās
    contacts.delete(db.connect(db_path), {"id": user_id(db_path, "admin@example.com")}, cid)
    html = client.get(f"/organizacijas/{oid}", headers=HTML).text
    assert "Dalībnieki: Dzēsta kontaktpersona" in html
    assert "Jānis Bērziņš" not in html


# --- MI-1 -----------------------------------------------------------------------


def test_ai_summary_prefills_form_and_is_labelled(client, db_path):
    login(client)
    oid = org_id(db_path)
    res = client.post(f"/organizacijas/{oid}/mijiedarbibas/jauna", data={"action": "ai", "notes": NOTES, "kind": "Sanāksme"}, headers=HTML)
    assert res.status_code == 200
    html = res.text
    assert "Ģenerēts ar MI" in html and "(imitācija)" in html
    assert "imitācijas režīmā" in html  # bez atslēgas teksts netiek sūtīts ārpus sistēmas
    assert 'name="ai_source" value="imitacija"' in html
    summary = re.search(r'<textarea id="summary"[^>]*>([^<]*)</textarea>', html).group(1)
    assert 0 < summary.count(".") <= 3
    assert "Jānosūta atbalsta pieteikuma veidlapa" in html  # nākamais solis
    assert "Apstiprināt un saglabāt" in html
    assert 'value="Sanāksme" required checked' in html  # pārējie lauki saglabājas
    assert q(db_path, "SELECT COUNT(*) FROM interactions WHERE ai_source IS NOT NULL")[0][0] == 0  # nekas nav saglabāts


def test_ai_summary_approved_on_save(client, db_path):
    login(client)
    oid = org_id(db_path)
    anna = user_id(db_path, "darbinieks@example.com")
    save(client, oid, staff=str(anna), summary="Rediģēts MI kopsavilkums.", ai_source="imitacija", notes=NOTES)
    row = q(db_path, "SELECT summary, ai_source, approved_by FROM interactions WHERE ai_source IS NOT NULL")[0]
    assert tuple(row) == ("Rediģēts MI kopsavilkums.", "imitacija", anna)
    assert NOTES[:30] not in str([tuple(r) for r in q(db_path, "SELECT * FROM interactions")])  # piezīmes nesaglabājas
    html = client.get(f"/organizacijas/{oid}", headers=HTML).text
    assert "Ģenerēts ar MI · apstiprināja Anna Kalniņa" in html
    actions = [r[0] for r in q(db_path, "SELECT action FROM access_log")]
    assert "ai_approve" in actions


def test_ai_generation_logged_without_text(client, db_path, caplog):
    login(client)
    client.post(f"/organizacijas/{org_id(db_path)}/mijiedarbibas/jauna", data={"action": "ai", "notes": NOTES}, headers=HTML)
    assert ("ai_generate",) in [tuple(r) for r in q(db_path, "SELECT action FROM access_log")]
    assert "talku" not in caplog.text


def test_ai_requires_notes(client, db_path):
    login(client)
    res = client.post(f"/organizacijas/{org_id(db_path)}/mijiedarbibas/jauna", data={"action": "ai", "notes": " "}, headers=HTML)
    assert res.status_code == 400
    assert "Ierakstiet piezīmes" in res.text


def test_imitation_contract():
    result = ai.kopsavilkums(NOTES)
    assert set(result) == {"kopsavilkums", "nakamais_solis", "avots"}
    assert result["avots"] == "imitacija"
    assert len([s for s in result["kopsavilkums"].split(". ") if s]) <= 3
    assert result["nakamais_solis"].startswith("Jānosūta")
    assert "Laikapstākļi" not in result["kopsavilkums"]  # mazsvarīgs teikums izlaists


def test_imitation_without_action_sentence():
    result = ai.kopsavilkums("Īsa saruna par sadarbību.")
    assert result["kopsavilkums"] == "Īsa saruna par sadarbību."
    assert result["nakamais_solis"] == ai.DEFAULT_NEXT_STEP


def test_claude_failure_falls_back_to_imitation(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setattr(ai, "_claude", lambda teksts: None)  # noildze, kļūda vai atteikums
    assert ai.kopsavilkums(NOTES)["avots"] == "imitacija"


def test_claude_result_used_when_available(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setattr(ai, "_claude", lambda teksts: {"kopsavilkums": "A. B.", "nakamais_solis": "C.", "avots": "claude"})
    assert ai.kopsavilkums(NOTES)["avots"] == "claude"


def test_dashboard_interactions_link_to_card(client, db_path):
    login(client)
    assert f'href="/organizacijas/{org_id(db_path)}#mijiedarbibas"' in client.get("/panelis", headers=HTML).text


# --- MI-1 imitācijas godīgums ----------------------------------------------------

CHATTY = "saņemts zvans un viņš teica bla bla bla, es bla bla, un beigās viņš nesaprata, bet es paskaidroju, saruna beidzās laimīgi."


def test_imitation_removes_fillers():
    result = ai.kopsavilkums(CHATTY)
    assert "bla" not in result["kopsavilkums"].lower()
    assert result["kopsavilkums"] == "Saņemts zvans, un beigās viņš nesaprata, bet es paskaidroju, saruna beidzās laimīgi."


def test_copy_detection():
    assert ai.parak_lidzigs(CHATTY, ai.kopsavilkums(CHATTY)["kopsavilkums"]) is True
    assert ai.parak_lidzigs(NOTES, ai.kopsavilkums(NOTES)["kopsavilkums"]) is False


def test_form_warns_when_imitation_only_copies(client, db_path):
    login(client)
    res = client.post(f"/organizacijas/{org_id(db_path)}/mijiedarbibas/jauna", data={"action": "ai", "notes": CHATTY}, headers=HTML)
    assert "Imitācija nespēja saīsināt šīs piezīmes" in res.text
    assert "Nākamais solis piezīmēs nav atrasts" in res.text


def test_form_has_no_warning_for_good_notes(client, db_path):
    login(client)
    res = client.post(f"/organizacijas/{org_id(db_path)}/mijiedarbibas/jauna", data={"action": "ai", "notes": NOTES}, headers=HTML)
    assert "nespēja saīsināt" not in res.text and "nav atrasts" not in res.text
