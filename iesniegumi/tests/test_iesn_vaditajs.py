"""US-5 pārskats vadītājam, US-6 piekļūstamības paziņojums."""

import re

from conftest import as_role


def test_report_only_for_manager(client):
    as_role(client, "darbinieks")
    assert client.get("/vaditajs/parskats").status_code == 403
    as_role(client, "vaditajs")
    assert client.get("/vaditajs/parskats").status_code == 200


def test_report_tables_and_average(vaditajs):
    html = vaditajs.get("/vaditajs/parskats").text
    assert "<caption>Iesniegumu skaits pa statusiem</caption>" in html
    assert "Iesniegumu skaits pa tēmām" in html
    assert re.search(r'status-jauns">Jauns</span></th><td class="num">3</td>', html)
    assert re.search(r'status-atbildets">Atbildēts</span></th><td class="num">4</td>', html)
    # Sākumdati: slēgtie apstrādāti 4, 2, 6, 8, 5 dienās → vidēji 5.0
    assert re.search(r'stat-value">5\.0</span>\s*<span class="stat-label">vidējais apstrādes laiks dienās \(5 slēgti', html)


def test_chart_has_text_alternative_and_same_data_as_table(vaditajs):
    html = vaditajs.get("/vaditajs/parskats").text
    assert re.search(r'<svg[^>]*role="img" aria-labelledby="chart-title chart-desc"', html)
    desc = re.search(r"<desc[^>]*>(.*?)</desc>", html, re.S).group(1)
    table = html.split("Iesniegumu skaits pa tēmām (tie paši dati")[1].split("</table>")[0]
    pairs = re.findall(r"([^.:]+): (\d+)\.", desc)
    assert len(pairs) == 6
    for label, n in pairs:
        assert f'<th scope="row">{label.strip()}</th><td class="num">{n}</td>' in table
    assert "<figcaption>" in html


def test_statement_page_and_footer_link(client):
    for path in ("/", "/iesniegt", "/mans-iesniegums"):
        assert 'href="/pieklustamiba"' in client.get(path).text, path
    html = client.get("/pieklustamiba").text
    for part in ("Ministru kabineta", "Nr. 445", "Daļēji atbilst", "Nepiekļūstamais saturs", "Piekļūstamības alternatīvas",
                 "Atsauksmēm un saziņai", "Sūdzību iesniegšana", "Tiesībsarga", "Ziņas par paziņojuma sagatavošanu",
                 "ekrānlasītāju"):
        assert part in html, part
