"""US-7 · MI ieteikums darbiniekam un pasākumi no MI riska novērtējuma."""

import ai
from conftest import q


def numurs_ar(app, statuss):
    return q(app, "SELECT numurs FROM iesniegumi WHERE statuss = ? ORDER BY id LIMIT 1", statuss)[0][0]


def test_contract_and_imitation_without_network(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    result = ai.ieteikums("Pie mājas ir liela bedre ceļā.")
    assert set(result) == {"tema", "atbildes_projekts"}
    assert result["tema"] == "Ceļi un bedres" and result["tema"] in ai.TEMAS
    assert ai.ieteikums_ar_avotu("lampa nedeg")[1] == "imitacija"


# Veidnes 6. sadaļa: 5 "grūti" iesniegumi, ar kuriem ieteikums var kļūdīties
# (nosaukums, teksts, pareizā tēma, ko dod imitācija). Rezultāti → docs/mi-riska-novertejums.md 5. nodaļa.
HARD_CASES = [
    ("Divdomīgs", "Pie bērnudārza ir tumšs, jo nedeg lampa.", "Ielu apgaismojums", "Ielu apgaismojums"),
    ("Vairākas problēmas", "Bedre ceļā un blakus pārpildīts atkritumu konteiners, kas netiek izvests.", "Ceļi un bedres / Atkritumi", "Atkritumi"),
    ("Sarkasms", "Paldies, ka mūsu ielā tagad ir 'ezers' — bedre tik liela, ka var makšķerēt.", "Ceļi un bedres", "Ceļi un bedres"),
    ("Bez atslēgvārdiem", "Kaimiņš katru nakti skaļi klausās mūziku.", "Cits", "Cits"),
    ("Sociālā + bērnudārzs", "Zaudēju darbu, nevaru samaksāt par bērnudārzu, vai ir kāds pabalsts?", "Sociālā palīdzība", "Bērnudārza rinda"),
]


def test_hard_cases_documented_behaviour(monkeypatch):
    """Dokumentē imitācijas uzvedību, arī kļūdas (pēdējais gadījums: sociālā palīdzība → bērnudārzs)."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    for _, text, _correct, observed in HARD_CASES:
        assert ai.ieteikums(text)["tema"] == observed, text


def test_ai_block_labelled_and_section(app, darbinieks):
    html = darbinieks.get(f"/darbinieks/iesniegumi/{numurs_ar(app, 'Jauns')}").text
    assert '<section class="ai-block" aria-labelledby="mi-virsraksts">' in html
    assert "Ģenerēts ar MI, pārbaudiet pirms lietošanas" in html
    assert "Ieteikums netiek nosūtīts un nemaina statusu" in html
    assert "spinner" not in html and "blink" not in html  # 2.3.1 bez mirgojoša indikatora


def test_use_projekts_fills_field_but_never_sends(app, darbinieks):
    n = numurs_ar(app, "Apstrādē")
    before = q(app, "SELECT statuss, atbilde, tema_id FROM iesniegumi WHERE numurs = ?", n)[0]
    res = darbinieks.post(f"/darbinieks/iesniegumi/{n}/mi-izmantot")
    assert res.status_code == 303
    after = q(app, "SELECT statuss, atbilde, tema_id, atbildes_projekts FROM iesniegumi WHERE numurs = ?", n)[0]
    assert (after["statuss"], after["atbilde"], after["tema_id"]) == tuple(before)  # nekas nav nosūtīts vai mainīts
    assert after["atbildes_projekts"].startswith("Labdien!")
    html = darbinieks.get(res.headers["Location"].split("#")[0]).text
    assert "MI projekts ielikts atbildes laukā. Pārbaudiet un rediģējiet" in html
    assert after["atbildes_projekts"].split("\n")[0] in html.split('id="atbilde"')[1]
    events = [r[0] for r in q(app, "SELECT veids FROM notikumi n JOIN iesniegumi i ON i.id = n.iesniegums_id WHERE numurs = ?", n)]
    assert "mi_izmantots" in events


def test_mi_topic_change_is_explicit_and_logged(app, darbinieks):
    # Iesniegums ar tēmu "Cits", kura apraksts ir par apgaismojumu
    conn_n = q(app, "SELECT numurs FROM iesniegumi WHERE apraksts LIKE '%lampas%' LIMIT 1")[0][0]
    import sqlite3
    c = sqlite3.connect(app.config["DB_PATH"]); c.execute("UPDATE iesniegumi SET tema_id = 6 WHERE numurs = ?", (conn_n,)); c.commit(); c.close()
    html = darbinieks.get(f"/darbinieks/iesniegumi/{conn_n}").text
    assert "Mainīt tēmu uz «Ielu apgaismojums»" in html
    darbinieks.post(f"/darbinieks/iesniegumi/{conn_n}/mi-tema")
    assert q(app, "SELECT tema_id FROM iesniegumi WHERE numurs = ?", conn_n)[0][0] == 2
    assert "mi_tema" in [r[0] for r in q(app, "SELECT veids FROM notikumi")]


def test_no_ai_block_on_closed(app, darbinieks):
    assert "MI ieteikums" not in darbinieks.get(f"/darbinieks/iesniegumi/{numurs_ar(app, 'Atbildēts')}").text


def test_claude_failure_falls_back(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test")
    monkeypatch.setattr(ai, "_claude", lambda t: None)
    assert ai.ieteikums_ar_avotu("bedre")[1] == "imitacija"
