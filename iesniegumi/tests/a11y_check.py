#!/usr/bin/env python3
"""US-9 · automātiskā pieejamības pārbaude (axe-core + Playwright) visām «Iesniegumi» lapām.

Pārbauda:
  A. axe-core ar WCAG 2.0/2.1/2.2 A un AA noteikumiem (arī formu ar kļūdām un lapu pēc statusa maiņas);
  B. tastatūru: pirmā Tab pietura ir "Pāriet uz saturu", fokuss redzams, iedzīvotāja ceļš tikai ar tastatūru,
     pēc kļūdas fokuss nonāk uz kļūdu kopsavilkumu;
  C. reflow: 320 px un 200 % mērogs (1280 px ekrāns → 640 CSS px) bez horizontālas ritināšanas.
Rezultāts: a11y-report.md un a11y-report.json (tos izmanto docs/pieejamibas-atskaite.md un /pieklustamiba).

Palaišana: make a11y   (vajag: pip install playwright axe-playwright-python && python -m playwright install chromium)
"""

from __future__ import annotations

import importlib.util
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

HERE = Path(__file__).resolve().parents[1]
sys.path.append(str(HERE))
_spec = importlib.util.spec_from_file_location("iesniegumi_app", HERE / "app.py")
iesniegumi_app = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(iesniegumi_app)

REPORT_MD = HERE / "a11y-report.md"
REPORT_JSON = HERE / "a11y-report.json"
AXE_TAGS = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"]
BLOCKING = {"critical", "serious"}
WIDTHS = {"320 px": 320, "200 %": 640}


def overflow(page: Page) -> int:
    return page.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")


def focus_problems(page: Page, limit: int = 50) -> list[str]:
    """WCAG 2.4.7: katram fokusējamam elementam redzama kontūra vai ēna."""
    problems = []
    page.evaluate("document.activeElement && document.activeElement.blur()")
    for _ in range(limit):
        page.keyboard.press("Tab")
        info = page.evaluate("""() => {
            const e = document.activeElement;
            if (!e || e === document.body) return null;
            const s = getComputedStyle(e);
            const ok = (s.outlineStyle !== 'none' && parseFloat(s.outlineWidth) > 0) || s.boxShadow !== 'none';
            return {ok, label: e.tagName.toLowerCase() + (e.id ? '#' + e.id : '') + ' "' + (e.innerText || e.value || '').trim().slice(0, 25) + '"'};
        }""")
        if info is None:
            break
        if not info["ok"]:
            problems.append(info["label"])
    return sorted(set(problems))


def choose_role(page: Page, base: str, role: str) -> None:
    page.goto(base + "/")
    with page.expect_navigation():
        page.click(f"button[value={role}]")


class Checker:
    def __init__(self, base: str):
        self.base = base
        self.axe = Axe()
        self.results: list[dict] = []
        self.engine = "?"

    def check(self, page: Page, title: str, url_label: str) -> None:
        if page.evaluate("document.body.innerText.trim()").startswith("US-") or "Lapa nav atrasta" in page.title():
            self.results.append({"title": title, "path": url_label, "skipped": True})
            return
        page.set_viewport_size({"width": 1280, "height": 900})
        resp = self.axe.run(page, options={"runOnly": {"type": "tag", "values": AXE_TAGS}}).response
        self.engine = resp["testEngine"]["version"]
        violations = [{"id": v["id"], "impact": v["impact"], "help": v["help"], "nodes": len(v["nodes"]),
                       "target": v["nodes"][0]["target"][0] if v["nodes"] else ""} for v in resp["violations"]]
        focus = focus_problems(page)
        widths = {}
        for label, w in WIDTHS.items():
            page.set_viewport_size({"width": w, "height": 700})
            widths[label] = overflow(page)
        page.set_viewport_size({"width": 1280, "height": 900})
        self.results.append({"title": title, "path": url_label, "skipped": False, "violations": violations,
                             "incomplete": len(resp["incomplete"]), "focus_not_visible": focus, "overflow_px": widths})


def keyboard_citizen_path(page: Page, base: str) -> list[tuple[str, bool, str]]:
    """Protokola B daļa: sākums → loma → iesniegt (ar kļūdu) → apstiprinājums → mans iesniegums, tikai ar tastatūru."""
    steps: list[tuple[str, bool, str]] = []
    page.goto(base + "/")
    page.keyboard.press("Tab")
    first = page.evaluate("document.activeElement.textContent.trim()")
    steps.append(("Pirmais Tab atver «Pāriet uz saturu»", first == "Pāriet uz saturu", first))

    def tab_to(js: str, limit: int = 80) -> bool:
        for _ in range(limit):
            page.keyboard.press("Tab")
            if page.evaluate(f"(e => {js})(document.activeElement)"):
                return True
        return False

    ok = tab_to("e.value === 'iedzivotajs'")
    if ok:
        with page.expect_navigation():
            page.keyboard.press("Enter")
    steps.append(("Loma izvēlēta ar Enter", ok and "/iesniegt" in page.url, page.url))
    if "/iesniegt" not in page.url or page.evaluate("document.body.innerText.trim()").startswith("US-"):
        return steps

    # Iesniedz tukšu formu ar Enter → fokusam jābūt uz kļūdu kopsavilkuma
    tab_to("e.id === 'vards'")
    with page.expect_navigation():
        page.keyboard.press("Enter")
    focused = page.evaluate("document.activeElement.id")
    steps.append(("Pēc kļūdas fokuss nonāk uz kļūdu kopsavilkumu", focused == "kludas", f"fokuss: #{focused}"))

    # Aizpilda formu tikai ar tastatūru
    tab_to("e.id === 'vards'"); page.keyboard.type("Anna Testere")
    tab_to("e.id === 'epasts'"); page.keyboard.type("anna@example.com")
    tab_to("e.id === 'tema'"); page.keyboard.press("ArrowDown")
    tab_to("e.id === 'vieta'"); page.keyboard.type("Ezera iela 5")
    tab_to("e.id === 'apraksts'"); page.keyboard.type("Pie mājas ir bedre.")
    tab_to("e.id === 'piekrisana'"); page.keyboard.press("Space")
    tab_to("e.type === 'submit' && e.closest('main')")
    with page.expect_navigation():
        page.keyboard.press("Enter")
    steps.append(("Formu var aizpildīt un iesniegt ar tastatūru", "/iesniegts/" in page.url, page.url))
    if "/iesniegts/" not in page.url:
        return steps

    ok = tab_to("e.tagName === 'A' && e.getAttribute('href').includes('mans-iesniegums?numurs=')")
    if ok:
        with page.expect_navigation():
            page.keyboard.press("Enter")
    steps.append(("No apstiprinājuma uz «Mans iesniegums» ar numuru", ok and "numurs=" in page.url, page.url))
    trapped = not tab_to("e.tagName === 'A' && e.textContent.includes('Piekļūstamības paziņojums')", limit=120)
    steps.append(("Nav vietas, kur fokuss «iestrēgst» (var aiziet līdz kājenei)", not trapped, ""))
    return steps


def main() -> int:
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    tmp = Path(tempfile.mkdtemp()) / "a11y.db"
    app = iesniegumi_app.create_app(tmp)
    server = make_server("127.0.0.1", 0, app, threaded=True)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{server.server_port}"
    numurs = "2026-0001"
    with app.app_context():
        conn = app.db()
        numurs = conn.execute("SELECT numurs FROM iesniegumi ORDER BY id LIMIT 1").fetchone()[0]
        jauns = conn.execute("SELECT numurs FROM iesniegumi WHERE statuss = 'Jauns' ORDER BY id LIMIT 1").fetchone()[0]

    checker = Checker(base)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context(viewport={"width": 1280, "height": 900}, locale="lv-LV")
        page = ctx.new_page()

        # Iedzīvotājs (bez lomas un ar lomu)
        for title, path in (("1 Sākumlapa: lomas izvēle", "/"), ("2 Iesnieguma forma", "/iesniegt"),
                            ("7 Piekļūstamības paziņojums", "/pieklustamiba"), ("8 Mans iesniegums", "/mans-iesniegums"),
                            ("8 Mans iesniegums: rezultāts", f"/mans-iesniegums?numurs={numurs}"),
                            ("8 Mans iesniegums: nav atrasts", "/mans-iesniegums?numurs=2099-9999")):
            page.goto(base + path)
            checker.check(page, title, path)

        page.goto(base + "/iesniegt")
        if page.locator("form#iesniegums").count():
            with page.expect_navigation():
                page.click("form#iesniegums button[type=submit]")
            checker.check(page, "2 Iesnieguma forma ar kļūdām", "POST /iesniegt (tukša)")
            page.goto(base + "/iesniegt")
            page.fill("#vards", "Anna Testere"); page.fill("#epasts", "anna@example.com")
            page.select_option("#tema", index=1); page.fill("#vieta", "Ezera iela 5")
            page.fill("#apraksts", "Pie mājas ir bedre."); page.check("#piekrisana")
            with page.expect_navigation():
                page.click("form#iesniegums button[type=submit]")
            checker.check(page, "3 Apstiprinājums", "/iesniegts/<numurs>")

        # Darbinieks
        choose_role(page, base, "darbinieks")
        for title, path in (("4 Saraksts", "/darbinieks/iesniegumi"),
                            ("4 Saraksts ar filtriem", "/darbinieks/iesniegumi?statuss=Jauns&tema=1&q=iela"),
                            ("5 Detaļas", f"/darbinieks/iesniegumi/{jauns}")):
            page.goto(base + path)
            checker.check(page, title, path)
        page.goto(base + f"/darbinieks/iesniegumi/{jauns}")
        if page.locator("form#statuss-forma").count():
            with page.expect_navigation():
                page.click("form#statuss-forma button[type=submit]")
            checker.check(page, "5 Detaļas pēc statusa maiņas", "POST statuss")
        if page.locator("form#mi-izmantot").count():
            with page.expect_navigation():
                page.click("form#mi-izmantot button[type=submit]")
            checker.check(page, "5 Detaļas: MI projekts atbildes laukā", "POST mi-izmantot")

        # Vadītājs
        choose_role(page, base, "vaditajs")
        page.goto(base + "/vaditajs/parskats")
        checker.check(page, "6 Pārskats vadītājam", "/vaditajs/parskats")
        ctx.close()

        ctx = browser.new_context(viewport={"width": 1280, "height": 900}, locale="lv-LV")
        keyboard = keyboard_citizen_path(ctx.new_page(), base)
        ctx.close()
        browser.close()
    server.shutdown()

    checked = [r for r in checker.results if not r["skipped"]]
    blocking = [(r["title"], v) for r in checked for v in r["violations"] if v["impact"] in BLOCKING]
    other = [(r["title"], v) for r in checked for v in r["violations"] if v["impact"] not in BLOCKING]
    overflow_rows = [(r["title"], k, px) for r in checked for k, px in r["overflow_px"].items() if px > 0]
    focus_rows = [(r["title"], r["focus_not_visible"]) for r in checked if r["focus_not_visible"]]
    keyboard_failed = [s for s in keyboard if not s[1]]
    summary = {"pages": len(checked), "skipped": len(checker.results) - len(checked),
               "blocking": len(blocking), "other": len(other), "overflow": len(overflow_rows),
               "focus": len(focus_rows), "keyboard_failed": len(keyboard_failed)}
    report = {"checked_at": datetime.now(timezone.utc).isoformat(timespec="minutes"), "axe_version": checker.engine,
              "tags": AXE_TAGS, "summary": summary, "pages": checker.results,
              "keyboard": [{"step": s, "ok": ok, "note": n} for s, ok, n in keyboard]}
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Pieejamības automātiskā testa atskaite (`tests/a11y_check.py`)", "",
        f"Pārbaudīts: {report['checked_at']} · axe-core {checker.engine} · WCAG 2.0/2.1/2.2 A un AA · Chromium (Playwright)", "",
        "## Kopsavilkums", "",
        "| Rādītājs | Vērtība |", "|---|---|",
        f"| Pārbaudītas lapas / stāvokļi | {summary['pages']} (izlaistas, vēl nav: {summary['skipped']}) |",
        f"| Critical/serious pārkāpumi | **{summary['blocking']}** |",
        f"| Moderate/minor pārkāpumi | {summary['other']} |",
        f"| Lapas ar horizontālu ritināšanu (320 px / 200 %) | {summary['overflow']} |",
        f"| Lapas ar neredzamu fokusu | {summary['focus']} |",
        f"| Tastatūras ceļa soļi, kas neizdevās | {summary['keyboard_failed']} |", "",
        "## Lapas", "",
        "| Lapa | axe pārkāpumi | Nepilnīgi (jāvērtē manuāli) | 320 px | 200 % | Fokuss |", "|---|---|---|---|---|---|",
    ]
    for r in checker.results:
        if r["skipped"]:
            lines.append(f"| {r['title']} | — vēl nav | — | — | — | — |")
            continue
        viol = "<br>".join(f"{v['impact']}: {v['id']} ({v['nodes']})" for v in r["violations"]) or "0"
        ov = {k: ("OK" if px <= 0 else f"+{px} px") for k, px in r["overflow_px"].items()}
        lines.append(f"| {r['title']} | {viol} | {r['incomplete']} | {ov['320 px']} | {ov['200 %']} | "
                     f"{'OK' if not r['focus_not_visible'] else ', '.join(r['focus_not_visible'])} |")
    lines += ["", "## Tastatūras ceļš (iedzīvotājs)", "", "| Pārbaude | Rezultāts | Piezīme |", "|---|---|---|"]
    lines += [f"| {s} | {'OK' if ok else 'Nē'} | {n} |" for s, ok, n in keyboard]
    if blocking or other:
        lines += ["", "## Atradumi", ""]
        lines += [f"- **{v['impact']}** · {title} · `{v['id']}` — {v['help']} (piem. `{v['target']}`)" for title, v in blocking + other]
    lines += ["", "Automātiskie rīki atrod tikai daļu problēmu. Ekrānlasītāja pārbaude (NVDA) jāveic cilvēkam — sk. docs/pieejamibas-atskaite.md.", ""]
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")

    print(f"Pārbaudītas {summary['pages']} lapas (izlaistas {summary['skipped']}) · axe {checker.engine}")
    for title, v in blocking + other:
        print(f"  [{v['impact']}] {title}: {v['id']} — {v['help']}")
    for title, label, px in overflow_rows:
        print(f"  [reflow] {title}: {label} +{px} px")
    for title, labels in focus_rows:
        print(f"  [fokuss] {title}: {', '.join(labels)}")
    for s, _, n in keyboard_failed:
        print(f"  [tastatūra] {s}: {n}")
    ok = not blocking and not overflow_rows and not focus_rows and not keyboard_failed
    print("OK: 0 critical/serious, reflow, fokuss, tastatūra" if ok else "IR ATRADUMI — sk. a11y-report.md")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
