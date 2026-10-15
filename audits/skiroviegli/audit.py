"""skiroviegli.lv piekļūstamības audits: axe-core (WCAG 2.2 AA) + tastatūra + reflow. Tikai lasīšana, viena caurlaide."""

import json
import re
import sys
from datetime import datetime, timezone

from axe_playwright_python.sync_playwright import Axe
from playwright.sync_api import sync_playwright

URL = "https://www.skiroviegli.lv/"
TAGS = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"]
OUT = sys.argv[1] if len(sys.argv) > 1 else "results.json"
axe = Axe()


def criteria(tags):
    out = []
    for t in tags:
        m = re.fullmatch(r"wcag(\d)(\d)(\d+)", t)
        if m:
            out.append(f"{m[1]}.{m[2]}.{m[3]}")
    return out


def run_axe(page):
    r = axe.run(page, options={"runOnly": {"type": "tag", "values": TAGS}}).response
    return r["testEngine"]["version"], [
        {"id": v["id"], "impact": v["impact"], "help": v["help"], "helpUrl": v["helpUrl"], "wcag": criteria(v["tags"]),
         "nodes": len(v["nodes"]), "targets": [", ".join(map(str, n["target"])) for n in v["nodes"][:3]],
         "html": [n["html"][:160] for n in v["nodes"][:2]]}
        for v in r["violations"]
    ], [{"id": v["id"], "nodes": len(v["nodes"])} for v in r["incomplete"]]


def overflow(page, width):
    page.set_viewport_size({"width": width, "height": 800})
    page.wait_for_timeout(800)
    return page.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")


def keyboard(page, n=25):
    page.evaluate("document.activeElement && document.activeElement.blur()")
    stops = []
    for _ in range(n):
        page.keyboard.press("Tab")
        stops.append(page.evaluate("""() => { const e = document.activeElement; if (!e || e === document.body) return null;
            const s = getComputedStyle(e);
            const visible = (s.outlineStyle !== 'none' && parseFloat(s.outlineWidth) > 0) || s.boxShadow !== 'none';
            return {el: e.tagName.toLowerCase() + (e.id ? '#' + e.id : '') + (e.className && typeof e.className === 'string' ? '.' + e.className.split(' ')[0] : ''),
                    text: (e.innerText || e.value || e.getAttribute('aria-label') || '').trim().replace(/\\s+/g, ' ').slice(0, 40), visible}; }"""))
    return stops


def fresh(page):
    page.set_viewport_size({"width": 1280, "height": 900})
    page.goto(URL, wait_until="networkidle", timeout=60000)
    page.wait_for_timeout(1500)


results = {"url": URL, "checked_at": datetime.now(timezone.utc).isoformat(timespec="minutes"), "states": []}
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1280, "height": 900}, locale="lv-LV")

    fresh(page)
    engine, v, inc = run_axe(page)
    results["axe_version"] = engine
    results["lang"] = page.evaluate("document.documentElement.getAttribute('lang')")
    results["title"] = page.title()
    results["landmarks"] = page.evaluate("() => ({header: document.querySelectorAll('header,[role=banner]').length, nav: document.querySelectorAll('nav,[role=navigation]').length, main: document.querySelectorAll('main,[role=main]').length, footer: document.querySelectorAll('footer,[role=contentinfo]').length})")
    results["headings"] = page.evaluate("() => [...document.querySelectorAll('h1,h2,h3,h4')].map(h => h.tagName + ': ' + h.innerText.trim().slice(0,60))")
    results["skip_link"] = page.evaluate("() => !![...document.querySelectorAll('a[href^=\"#\"]')].find(a => /satur|content|galven/i.test(a.innerText))")
    stops = keyboard(page)
    results["states"].append({"name": "1 Sākumlapa", "violations": v, "incomplete": inc, "keyboard": stops,
                              "overflow_320": overflow(page, 320), "overflow_640": overflow(page, 640)})

    for name, label, modal in (("2 Piekļūstamības paziņojums (dialogs)", "Piekļūstamība", "#accessibilityModal"),
                               ("3 Informācija operatoriem (dialogs)", "Informācija operatoriem", None)):
        fresh(page)
        page.get_by_text(label, exact=True).first.click()
        page.wait_for_timeout(1500)
        engine, v, inc = run_axe(page)
        focus = page.evaluate("document.activeElement.outerHTML.slice(0, 120)")
        stops = keyboard(page, 12)
        results["states"].append({"name": name, "violations": v, "incomplete": inc, "focus_on_open": focus, "keyboard": stops,
                                  "overflow_320": overflow(page, 320), "overflow_640": overflow(page, 640)})

    fresh(page)
    page.get_by_role("button", name="Visa Latvija").first.click()
    page.wait_for_timeout(1000)
    engine, v, inc = run_axe(page)
    results["states"].append({"name": "4 Karte: pašvaldību filtrs atvērts", "violations": v, "incomplete": inc,
                              "overflow_320": overflow(page, 320), "overflow_640": overflow(page, 640)})

    page.set_viewport_size({"width": 320, "height": 800})
    page.goto(URL, wait_until="networkidle", timeout=60000)
    page.wait_for_timeout(1500)
    engine, v, inc = run_axe(page)
    page.screenshot(path="home-320.png", full_page=False)
    results["states"].append({"name": "5 Sākumlapa 320 px platumā", "violations": v, "incomplete": inc,
                              "overflow_320": page.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")})
    browser.close()

json.dump(results, open(OUT, "w"), ensure_ascii=False, indent=2)
print("lang:", repr(results["lang"]), "| title:", results["title"], "| landmarks:", results["landmarks"], "| skip link:", results["skip_link"])
for s in results["states"]:
    print(f"\n== {s['name']} · overflow320={s.get('overflow_320')} overflow640={s.get('overflow_640')}")
    for x in s["violations"]:
        print(f"  [{x['impact']}] {x['id']} {x['wcag']} ×{x['nodes']} — {x['help']} · {x['targets'][:2]}")
    if s.get("incomplete"):
        print("  nepilnīgi:", s["incomplete"])
    if s.get("focus_on_open"):
        print("  fokuss pēc atvēršanas:", s["focus_on_open"][:90])
    if s.get("keyboard"):
        ks = [k for k in s["keyboard"] if k]
        print("  Tab:", [(k["el"][:30], k["text"][:20], "redzams" if k["visible"] else "NEREDZAMS") for k in ks[:8]])
        print("  neredzams fokuss:", sum(1 for k in ks if not k["visible"]), "no", len(ks))
