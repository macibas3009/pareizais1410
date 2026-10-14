#!/usr/bin/env python3
"""N1 · automātiskā piekļūstamības pārbaude (axe-core + Playwright).

Palaiž lietotni ar sintētiskiem sākumdatiem pagaidu datubāzē un pārbauda galvenos ekrānus:
  1. axe-core ar WCAG 2.0/2.1/2.2 A un AA noteikumiem: nedrīkst būt "critical" vai "serious";
  2. 320 px platums un 200 % mērogs (1280 px ekrāns → 640 CSS px): bez horizontālas ritināšanas;
  3. tastatūra: pirmā Tab pietura ir "Pāriet uz saturu", fokuss vienmēr redzams,
     galvenais ceļš (pieslēgšanās → organizācija → mijiedarbība → pieprasījums → uzdevums) tikai ar tastatūru.

Rezultātu raksta docs/a11y-rezultati.json; to rāda lapa /pieklustamiba (F8).
Palaišana: make a11y   (vajag: pip install playwright axe-playwright-python && playwright install chromium)
"""

from __future__ import annotations

import json
import logging
import sys
import tempfile
import threading
from datetime import datetime, timezone
from pathlib import Path

from axe_playwright_python.sync_playwright import Axe
from playwright.sync_api import Page, sync_playwright
from werkzeug.serving import make_server

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import db, seed  # noqa: E402
from app.main import create_app  # noqa: E402

REPORT = ROOT / "docs" / "a11y-rezultati.json"
AXE_TAGS = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"]
BLOCKING = {"critical", "serious"}
WIDTHS = {"320 px": 320, "200 % mērogs": 640}


def pages(conn) -> dict[str, list[tuple[str, str]]]:
    one = lambda sql: conn.execute(sql).fetchone()[0]  # noqa: E731
    org = one("SELECT id FROM organizations ORDER BY id LIMIT 1")
    contact = one(f"SELECT id FROM contacts WHERE organization_id = {org} LIMIT 1")
    req = one(f"SELECT id FROM requests WHERE organization_id = {org} LIMIT 1")
    return {
        "": [("Pieslēgties", "/login"), ("Reģistrēties", "/register"), ("Piekļūstamības paziņojums", "/pieklustamiba")],
        "darbinieks@example.com": [
            ("Vadības panelis (darbinieks)", "/panelis"),
            ("Organizāciju saraksts", "/organizacijas"),
            ("Organizācijas kartīte", f"/organizacijas/{org}"),
            ("Organizācijas forma", f"/organizacijas/{org}/labot"),
            ("Kontaktpersonas kartīte", f"/kontakti/{contact}"),
            ("Kontaktpersonas forma", f"/organizacijas/{org}/kontakti/jauns"),
            ("Mijiedarbības forma", f"/organizacijas/{org}/mijiedarbibas/jauna"),
            ("Pieprasījumu saraksts", "/pieprasijumi"),
            ("Pieprasījuma kartīte", f"/pieprasijumi/{req}"),
            ("Pieprasījuma forma", f"/organizacijas/{org}/pieprasijumi/jauns"),
            ("Mani uzdevumi", "/uzdevumi"),
            ("Uzdevuma forma", "/uzdevumi/jauns"),
            ("Kontakti, kas jāpārskata", "/kontakti/japarskata"),
            ("Meklēšanas rezultāti", "/meklet?q=ezer"),
        ],
        "vaditajs@example.com": [("Vadības panelis (vadītājs)", "/panelis"), ("Vadītāja pārskats", "/parskats")],
        "admin@example.com": [
            ("Vadības panelis (administrators)", "/panelis"),
            ("Lietotāji un lomas", "/lietotaji"),
            ("Dzēšanas pieprasījumi", "/dzesanas-pieprasijumi"),
            ("Piekļuves žurnāls", "/zurnals"),
        ],
    }


def login(page: Page, base: str, email: str) -> None:
    page.goto(base + "/login")
    page.fill("#email", email)
    page.fill("#password", seed.SEED_PASSWORD)
    with page.expect_navigation():
        page.click("main button[type=submit]")


def overflow(page: Page) -> int:
    return page.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")


def unfocused_style_problems(page: Page, limit: int = 40) -> list[str]:
    """Tab cauri lapai: katram elementam ar fokusu jābūt redzamam kontūram vai ēnai (WCAG 2.4.7)."""
    problems = []
    page.evaluate("document.activeElement && document.activeElement.blur()")
    for _ in range(limit):
        page.keyboard.press("Tab")
        info = page.evaluate("""() => {
            const e = document.activeElement;
            if (!e || e === document.body) return null;
            const s = getComputedStyle(e);
            const visible = (s.outlineStyle !== 'none' && parseFloat(s.outlineWidth) > 0) || s.boxShadow !== 'none';
            return {visible, label: e.tagName.toLowerCase() + (e.id ? '#' + e.id : '') + ' "' + (e.innerText || e.value || '').trim().slice(0, 30) + '"'};
        }""")
        if info is None:
            break
        if not info["visible"]:
            problems.append(info["label"])
    return sorted(set(problems))


def keyboard_main_path(page: Page, base: str, own_org: int) -> list[str]:
    """Galvenais ceļš tikai ar tastatūru. Atgriež soļus, kas neizdevās."""
    failed = []
    page.goto(base + "/login")
    page.keyboard.press("Tab")
    if page.evaluate("document.activeElement.textContent.trim()") != "Pāriet uz saturu":
        failed.append("pirmā Tab pietura nav \"Pāriet uz saturu\"")

    def tab_to(predicate_js: str, max_tabs: int = 60) -> bool:
        for _ in range(max_tabs):
            page.keyboard.press("Tab")
            if page.evaluate(f"(e => {predicate_js})(document.activeElement)"):
                return True
        return False

    tab_to("e.id === 'email'"); page.keyboard.type("darbinieks@example.com")
    page.keyboard.press("Tab"); page.keyboard.type(seed.SEED_PASSWORD)
    with page.expect_navigation():
        page.keyboard.press("Enter")
    if not page.url.endswith("/panelis"):
        failed.append("pieslēgšanās ar tastatūru")
        return failed

    steps = [
        ("atvērt Organizācijas", "e.tagName === 'A' && e.getAttribute('href') === '/organizacijas'", "/organizacijas"),
        ("atvērt savas organizācijas kartīti", f"e.tagName === 'A' && e.getAttribute('href') === '/organizacijas/{own_org}'", f"/organizacijas/{own_org}"),
        ("atvērt mijiedarbības formu", "e.tagName === 'A' && /mijiedarbibas\\/jauna$/.test(e.getAttribute('href'))", "/mijiedarbibas/jauna"),
    ]
    for name, predicate, expect in steps:
        if not tab_to(predicate):
            failed.append(name)
            return failed
        with page.expect_navigation():
            page.keyboard.press("Enter")
        if expect not in page.url:
            failed.append(name)
            return failed

    # Aizpilda mijiedarbību: veids ar bultiņām, kopsavilkums, saglabāšana
    tab_to("e.name === 'kind'"); page.keyboard.press("Space")
    tab_to("e.id === 'summary'"); page.keyboard.type("Saruna pa tālruni par talku.")
    tab_to("e.tagName === 'BUTTON' && e.value === 'save'")
    with page.expect_navigation():
        page.keyboard.press("Enter")
    if "mijiedarbiba=1" not in page.url:
        failed.append("saglabāt mijiedarbību ar tastatūru")
        return failed

    if not tab_to("e.tagName === 'A' && /pieprasijumi\\/jauns$/.test(e.getAttribute('href'))"):
        failed.append("atvērt pieprasījuma formu")
        return failed
    with page.expect_navigation():
        page.keyboard.press("Enter")
    tab_to("e.id === 'subject'"); page.keyboard.type("Telpas semināram")
    tab_to("e.tagName === 'BUTTON' && e.type === 'submit' && e.closest('main')")
    with page.expect_navigation():
        page.keyboard.press("Enter")
    if "/pieprasijumi/" not in page.url:
        failed.append("izveidot pieprasījumu ar tastatūru")
        return failed

    if not tab_to("e.tagName === 'A' && /uzdevumi\\/jauns/.test(e.getAttribute('href'))"):
        failed.append("atvērt uzdevuma formu")
        return failed
    with page.expect_navigation():
        page.keyboard.press("Enter")
    tab_to("e.id === 'description'"); page.keyboard.type("Rezervēt zāli")
    tab_to("e.tagName === 'BUTTON' && e.type === 'submit' && e.closest('main')")
    with page.expect_navigation():
        page.keyboard.press("Enter")
    if "Rezervēt zāli" not in page.content():
        failed.append("izveidot uzdevumu ar tastatūru")
    return failed


def main() -> int:
    tmp = Path(tempfile.mkdtemp()) / "a11y.db"
    conn = db.connect(tmp)
    seed.seed(conn)
    app = create_app(db_path=tmp)
    logging.getLogger("werkzeug").setLevel(logging.WARNING)  # bez pieprasījumu žurnāla izvadē
    server = make_server("127.0.0.1", 0, app, threaded=True)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{server.server_port}"
    axe = Axe()

    results = []
    engine_version = "?"
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for email, items in pages(conn).items():
            context = browser.new_context(viewport={"width": 1280, "height": 900}, locale="lv-LV")
            page = context.new_page()
            if email:
                login(page, base, email)
            for title, path in items:
                page.set_viewport_size({"width": 1280, "height": 900})
                page.goto(base + path)
                axe_result = axe.run(page, options={"runOnly": {"type": "tag", "values": AXE_TAGS}}).response
                engine_version = axe_result["testEngine"]["version"]
                violations = [
                    {"id": v["id"], "impact": v["impact"], "help": v["help"], "nodes": len(v["nodes"]),
                     "example": v["nodes"][0]["target"][0] if v["nodes"] else ""}
                    for v in axe_result["violations"]
                ]
                focus = unfocused_style_problems(page)
                widths = {}
                for label, width in WIDTHS.items():
                    page.set_viewport_size({"width": width, "height": 700})
                    widths[label] = overflow(page)
                results.append({"title": title, "path": path, "violations": violations,
                                "incomplete": len(axe_result["incomplete"]), "focus_not_visible": focus,
                                "horizontal_overflow_px": widths})
            context.close()

        context = browser.new_context(viewport={"width": 1280, "height": 900}, locale="lv-LV")
        own_org = conn.execute(
            "SELECT o.id FROM organizations o JOIN users u ON u.id = o.responsible_id "
            "WHERE u.email = 'darbinieks@example.com' ORDER BY o.id LIMIT 1").fetchone()[0]
        keyboard_failed = keyboard_main_path(context.new_page(), base, own_org)
        context.close()
        browser.close()
    server.shutdown()

    blocking = [(r["title"], v["id"], v["impact"]) for r in results for v in r["violations"] if v["impact"] in BLOCKING]
    other = [(r["title"], v["id"], v["impact"]) for r in results for v in r["violations"] if v["impact"] not in BLOCKING]
    overflow_pages = [(r["title"], k, px) for r in results for k, px in r["horizontal_overflow_px"].items() if px > 0]
    focus_pages = [(r["title"], r["focus_not_visible"]) for r in results if r["focus_not_visible"]]
    report = {
        "checked_at": datetime.now(timezone.utc).isoformat(timespec="minutes"),
        "axe_version": engine_version,
        "standard": "WCAG 2.2 AA (axe tags: " + ", ".join(AXE_TAGS) + ")",
        "pages": results,
        "summary": {
            "pages": len(results),
            "blocking_violations": len(blocking),
            "other_violations": len(other),
            "overflow_pages": len(overflow_pages),
            "focus_problem_pages": len(focus_pages),
            "keyboard_main_path_failed": keyboard_failed,
        },
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"Pārbaudītas lapas: {len(results)} · axe {report['axe_version']} · {report['standard']}")
    for title, rule, impact in blocking + other:
        print(f"  [{impact}] {title}: {rule}")
    for title, label, px in overflow_pages:
        print(f"  [platums] {title}: {label} +{px} px")
    for title, labels in focus_pages:
        print(f"  [fokuss] {title}: {', '.join(labels)}")
    for step in keyboard_failed:
        print(f"  [tastatūra] neizdevās: {step}")
    ok = not blocking and not overflow_pages and not focus_pages and not keyboard_failed
    print("OK: nav critical/serious, nav horizontālas ritināšanas, fokuss redzams, galvenais ceļš ar tastatūru" if ok else "KĻŪDAS — sk. augstāk")
    print(f"Rezultāts: {REPORT.relative_to(ROOT)}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
