#!/usr/bin/env python3
"""Pieejamības protokola daļas, ko var pārbaudīt automātiski (docs/PIEEJAMIBAS-PRASIBAS.md 3.–4. sadaļa).

Papildina tests/a11y_check.py (axe). Pārbauda to, ko ekrānlasītājs un tastatūra "redz":
  D1 lapu nosaukumi un to unikalitāte (2.4.2) · D2 virsrakstu secība (1.3.1, 2.4.6) · D3 orientieri
  D4 formu lauku pieejamais nosaukums, obligātums, kļūdas apraksts (pieejamības koks) · 2.5.8 mērķu izmērs ≥ 24 px
  4.1.3 paziņojums pēc darbības: vai tas ir lapas nosaukumā / role=status
Ekrānlasītāju (NVDA) tas neaizstāj. Rezultāts: a11y-protokols.json
"""

from __future__ import annotations

import importlib.util
import json
import logging
import sys
import tempfile
import threading
from pathlib import Path

from playwright.sync_api import Page, sync_playwright
from werkzeug.serving import make_server

HERE = Path(__file__).resolve().parents[1]
sys.path.append(str(HERE))
_spec = importlib.util.spec_from_file_location("iesniegumi_app", HERE / "app.py")
iesniegumi_app = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(iesniegumi_app)
OUT = HERE / "a11y-protokols.json"

HEADINGS_JS = "() => [...document.querySelectorAll('h1,h2,h3,h4')].map(h => [Number(h.tagName[1]), h.textContent.trim().slice(0,60)])"
LANDMARKS_JS = """() => ({banner: !!document.querySelector('header'), navigation: !!document.querySelector('nav'),
                    main: document.querySelectorAll('main').length, contentinfo: !!document.querySelector('footer')})"""
TARGETS_JS = """() => [...document.querySelectorAll('button, input, select, textarea, a.btn, nav a, .role-box a')]
  .filter(e => e.offsetParent !== null && e.type !== 'hidden')
  .map(e => { const r = e.getBoundingClientRect(); return {el: e.tagName.toLowerCase() + (e.id ? '#' + e.id : '') + (e.type ? '[' + e.type + ']' : ''),
                                                           w: Math.round(r.width), h: Math.round(r.height)}; })
  .filter(t => t.w < 24 || t.h < 24)"""
FIELDS_JS = """() => [...document.querySelectorAll('main input:not([type=hidden]), main select, main textarea')].map(e => {
   const label = e.labels && e.labels[0] ? e.labels[0].textContent.replace(/\\s+/g, ' ').trim() : '';
   const desc = (e.getAttribute('aria-describedby') || '').split(' ').filter(Boolean)
                  .map(id => (document.getElementById(id) || {}).textContent || '').join(' ').replace(/\\s+/g, ' ').trim();
   return {id: e.id, name: label, required: e.required, invalid: e.getAttribute('aria-invalid') === 'true', description: desc};
})"""


def heading_problems(levels: list) -> list[str]:
    problems = []
    if not levels or levels[0][0] != 1:
        problems.append("pirmais virsraksts nav h1")
    if sum(1 for lvl, _ in levels if lvl == 1) != 1:
        problems.append("nav tieši viens h1")
    for (a, _), (b, text) in zip(levels, levels[1:]):
        if b > a + 1:
            problems.append(f"izlaists līmenis pirms h{b} «{text}»")
    return problems


def snapshot(page: Page, title: str) -> dict:
    levels = page.evaluate(HEADINGS_JS)
    return {"title": title, "url": page.url.split("//", 1)[1].split("/", 1)[1], "page_title": page.title(),
            "headings": levels, "heading_problems": heading_problems(levels), "landmarks": page.evaluate(LANDMARKS_JS),
            "small_targets": page.evaluate(TARGETS_JS), "fields": page.evaluate(FIELDS_JS)}


def main() -> int:
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    app = iesniegumi_app.create_app(Path(tempfile.mkdtemp()) / "p.db")
    server = make_server("127.0.0.1", 0, app, threaded=True)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{server.server_port}"
    with app.app_context():
        jauns = app.db().execute("SELECT numurs FROM iesniegumi WHERE statuss = 'Jauns' LIMIT 1").fetchone()[0]

    pages = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        for title, path in (("Sākumlapa", "/"), ("Iesnieguma forma", "/iesniegt"), ("Mans iesniegums", "/mans-iesniegums"),
                            ("Paziņojums", "/pieklustamiba")):
            page.goto(base + path); pages.append(snapshot(page, title))
        page.goto(base + "/iesniegt")
        with page.expect_navigation():
            page.click("form#iesniegums button[type=submit]")
        pages.append(snapshot(page, "Iesnieguma forma ar kļūdām"))
        page.fill("#vards", "Anna Testere"); page.fill("#epasts", "anna@example.com"); page.select_option("#tema", index=1)
        page.fill("#vieta", "Ezera iela 5"); page.fill("#apraksts", "Bedre."); page.check("#piekrisana")
        with page.expect_navigation():
            page.click("form#iesniegums button[type=submit]")
        pages.append(snapshot(page, "Apstiprinājums"))
        page.goto(base + "/");
        with page.expect_navigation():
            page.click("button[value=darbinieks]")
        pages.append(snapshot(page, "Saraksts"))
        page.goto(base + f"/darbinieks/iesniegumi/{jauns}"); pages.append(snapshot(page, "Detaļas"))
        with page.expect_navigation():
            page.click("form#statuss-forma button[type=submit]")
        after = snapshot(page, "Detaļas pēc statusa maiņas")
        after["status_region"] = page.evaluate("(document.querySelector('[role=status]') || {}).innerText || ''")
        after["focused_after_reload"] = page.evaluate("document.activeElement.tagName.toLowerCase() + (document.activeElement.id ? '#' + document.activeElement.id : '')")
        pages.append(after)
        page.goto(base + "/")
        with page.expect_navigation():
            page.click("button[value=vaditajs]")
        pages.append(snapshot(page, "Pārskats"))
        browser.close()
    server.shutdown()

    titles = [pg["page_title"] for pg in pages]
    result = {"pages": pages, "duplicate_titles": sorted({t for t in titles if titles.count(t) > 1})}
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    for pg in pages:
        issues = pg["heading_problems"] + [f"mazs mērķis {t['el']} {t['w']}×{t['h']}" for t in pg["small_targets"]]
        lm = pg["landmarks"]
        if not (lm["banner"] and lm["navigation"] and lm["main"] == 1 and lm["contentinfo"]):
            issues.append(f"orientieri: {lm}")
        issues += [f"laukam #{f['id']} nav nosaukuma" for f in pg["fields"] if not f["name"]]
        issues += [f"laukam #{f['id']} kļūda bez apraksta" for f in pg["fields"] if f["invalid"] and "Kļūda" not in f["description"] and not f["description"]]
        print(f"{pg['title']:32} «{pg['page_title'][:55]}» {'OK' if not issues else '; '.join(issues)}")
        if "status_region" in pg:
            print(f"{'':32} role=status: «{pg['status_region']}» · fokuss pēc pārlādes: {pg['focused_after_reload']}")
    if result["duplicate_titles"]:
        print("Dublēti lapu nosaukumi:", result["duplicate_titles"])
    print(f"Rezultāts: {OUT.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
