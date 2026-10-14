"""US-3 saraksts, US-4 detaļas un apstrāde."""

import re

from conftest import HTML, as_role, q


def numurs_ar(app, statuss):
    return q(app, "SELECT numurs FROM iesniegumi WHERE statuss = ? ORDER BY id LIMIT 1", statuss)[0][0]


# --- US-3 ----------------------------------------------------------------------------


def test_list_requires_staff_role(client):
    assert client.get("/darbinieks/iesniegumi").status_code == 303  # bez lomas → sākumlapa
    as_role(client, "iedzivotajs")
    assert client.get("/darbinieks/iesniegumi").status_code == 403


def test_list_table_semantics(darbinieks):
    html = darbinieks.get("/darbinieks/iesniegumi").text
    assert "<caption>Iesniegumi: 10</caption>" in html
    assert html.count('scope="col"') == 5 and 'scope="row"' in html
    assert re.search(r'>Iesniegums \d{4}-\d{4}</a>', html)          # 2.4.4
    assert ">Skatīt<" not in html
    assert '<fieldset class="filters">' in html and "<legend>Filtrēt iesniegumus</legend>" in html
    assert 'class="status status-jauns">Jauns</span>' in html        # 1.4.1 statuss tekstā


def test_newest_first(app, darbinieks):
    html = darbinieks.get("/darbinieks/iesniegumi").text
    nums = re.findall(r">Iesniegums (\d{4}-\d{4})<", html)
    assert nums == sorted(nums, reverse=True)


def test_filters_and_search(darbinieks):
    assert "Iesniegumi: 4 (filtrēts)" in darbinieks.get("/darbinieks/iesniegumi?statuss=Atbildēts").text
    assert "Iesniegumi: 2 (filtrēts)" in darbinieks.get("/darbinieks/iesniegumi?tema=1").text
    html = darbinieks.get("/darbinieks/iesniegumi?q=LAMPA").text  # reģistrs nav svarīgs ("lampas", "lampa")
    assert "Iesniegumi: 2 (filtrēts)" in html
    assert "Iesniegumi: 1 (filtrēts)" in darbinieks.get("/darbinieks/iesniegumi?q=bērziņš").text
    assert "Iesniegumi: 0 (filtrēts)" in darbinieks.get("/darbinieks/iesniegumi?q=%25%25").text
    assert "Neviens iesniegums neatbilst filtriem." in darbinieks.get("/darbinieks/iesniegumi?q=zzzz").text


# --- US-4 ----------------------------------------------------------------------------


def test_detail_heading_hierarchy(app, darbinieks):
    html = darbinieks.get(f"/darbinieks/iesniegumi/{numurs_ar(app, 'Jauns')}").text
    assert html.count("<h1>") == 1
    assert "<h2 id=\"dati\">" in html and "<h2 id=\"apstrade\">" in html and "<h2 id=\"vesture\">" in html
    assert 'role="status"' in html
    assert "Sākt apstrādi: mainīt statusu uz «Apstrādē»" in html     # 4.1.2 skaidrs pogas teksts


def test_status_flow_and_events(app, darbinieks):
    n = numurs_ar(app, "Jauns")
    res = darbinieks.post(f"/darbinieks/iesniegumi/{n}/statuss", data={"statuss": "Apstrādē"})
    assert res.status_code == 303 and "pazinojums=statuss" in res.headers["Location"]
    html = darbinieks.get(res.headers["Location"].split("#")[0]).text
    assert 'role="status" tabindex="-1"><p class="alert ok">Statuss nomainīts uz «Apstrādē».' in html  # 4.1.3
    res = darbinieks.post(f"/darbinieks/iesniegumi/{n}/statuss", data={"statuss": "Atbildēts", "atbilde": "Bedre salabota."})
    assert res.status_code == 303
    row = q(app, "SELECT statuss, atbilde, slegts FROM iesniegumi WHERE numurs = ?", n)[0]
    assert row["statuss"] == "Atbildēts" and row["atbilde"] == "Bedre salabota." and row["slegts"]
    events = [r[0] for r in q(app, "SELECT n.apraksts FROM notikumi n JOIN iesniegumi i ON i.id = n.iesniegums_id WHERE numurs = ? ORDER BY n.id", n)]
    assert events[-2:] == ["Statuss: Jauns → Apstrādē", "Statuss: Apstrādē → Atbildēts"]


def test_illegal_transitions(app, darbinieks):
    n = numurs_ar(app, "Jauns")
    assert darbinieks.post(f"/darbinieks/iesniegumi/{n}/statuss", data={"statuss": "Atbildēts", "atbilde": "x"}).status_code == 400
    closed = numurs_ar(app, "Atbildēts")
    assert darbinieks.post(f"/darbinieks/iesniegumi/{closed}/statuss", data={"statuss": "Apstrādē"}).status_code == 400


def test_answer_and_rejection_need_text(app, darbinieks):
    n = numurs_ar(app, "Apstrādē")
    res = darbinieks.post(f"/darbinieks/iesniegumi/{n}/statuss", data={"statuss": "Noraidīts", "atbilde": " "})
    assert res.status_code == 400 and "Ierakstiet noraidījuma pamatojumu" in res.text
    assert 'aria-invalid="true"' in res.text


def test_draft_and_comment(app, darbinieks):
    n = numurs_ar(app, "Apstrādē")
    darbinieks.post(f"/darbinieks/iesniegumi/{n}/projekts", data={"atbilde": "Melnraksts"})
    assert q(app, "SELECT statuss, atbildes_projekts FROM iesniegumi WHERE numurs = ?", n)[0][:] == ("Apstrādē", "Melnraksts")
    assert "Melnraksts</textarea>" in darbinieks.get(f"/darbinieks/iesniegumi/{n}").text
    darbinieks.post(f"/darbinieks/iesniegumi/{n}/komentars", data={"komentars": "Piezvanīju iedzīvotājam"})
    html = darbinieks.get(f"/darbinieks/iesniegumi/{n}").text
    assert "Komentārs: Piezvanīju iedzīvotājam" in html
    assert "Pievienot komentāru" in html
    # Komentārs ir iekšējs: iedzīvotājs to neredz
    assert "Piezvanīju" not in darbinieks.get(f"/mans-iesniegums?numurs={n}").text


def test_history_chronological(app, darbinieks):
    n = numurs_ar(app, "Atbildēts")
    html = darbinieks.get(f"/darbinieks/iesniegumi/{n}").text
    timeline = html.split('class="timeline"')[1]
    assert timeline.index("Iesniegums reģistrēts") < timeline.index("Jauns → Apstrādē") < timeline.index("Apstrādē → Atbildēts")


def test_no_fixed_header(app):
    css = open(app.root_path + "/static/style.css", encoding="utf-8").read()
    assert "position: fixed" not in css and "position: sticky" not in css  # 2.4.11


# --- Pieejamības labojumi pēc testēšanas (atradumi #1–#3) ---------------------------


def test_notice_in_title_and_focus_after_status_change(app, darbinieks):
    n = numurs_ar(app, "Jauns")
    loc = darbinieks.post(f"/darbinieks/iesniegumi/{n}/statuss", data={"statuss": "Apstrādē"}).headers["Location"]
    html = darbinieks.get(loc.split("#")[0]).text
    assert f"<title>Statuss nomainīts uz «Apstrādē»: Iesniegums {n}" in html
    assert 'id="pazinojums" role="status" tabindex="-1"' in html
    assert 'document.getElementById("pazinojums").focus()' in html


def test_titles_are_descriptive(darbinieks):
    html = darbinieks.get("/darbinieks/iesniegumi").text
    assert "<title>Iesniegumu saraksts · Ezermalas novada pašvaldība</title>" in html
