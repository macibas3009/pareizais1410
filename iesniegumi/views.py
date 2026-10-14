"""Ekrāni 2–8. Katra US maršruti savā sadaļā."""

from __future__ import annotations

import json
import math
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, abort, redirect, render_template, request, url_for

import ai

NAME_RE = re.compile(r"^[^\W\d_]+(?:[ '\-.][^\W\d_]+)*\.?$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
NUMURS_RE = re.compile(r"^\d{4}-\d{4}$")
APRAKSTS_MAX = 3000

FIELD_LABELS = {
    "vards": "Vārds, uzvārds",
    "epasts": "E-pasts",
    "tema": "Tēma",
    "vieta": "Adrese vai vieta",
    "apraksts": "Apraksts",
    "piekrisana": "Piekrišana datu apstrādei",
}
# US-1: kļūdas saka, KĀ labot (WCAG 3.3.3)
MESSAGES = {
    ("vards", "REQUIRED"): "Ierakstiet savu vārdu un uzvārdu.",
    ("vards", "FORMAT"): "Vārdā drīkst būt tikai burti, atstarpes un defise, piemēram, Līga Ozoliņa-Kalniņa.",
    ("epasts", "REQUIRED"): "Ierakstiet e-pasta adresi, uz kuru sūtīsim atbildi.",
    ("epasts", "FORMAT"): "Ievadiet e-pastu formā vards@domens.lv.",
    ("tema", "REQUIRED"): "Izvēlieties tēmu no saraksta. Ja neviena neder, izvēlieties «Cits».",
    ("vieta", "REQUIRED"): "Ierakstiet adresi vai vietas aprakstu, piemēram, «Ezera iela 12» vai «pie stacijas».",
    ("apraksts", "REQUIRED"): "Aprakstiet, kas noticis vai ko lūdzat.",
    ("apraksts", "TOO_LONG"): f"Apraksts ir par garu: ne vairāk kā {APRAKSTS_MAX} rakstzīmes.",
    ("piekrisana", "REQUIRED"): "Atzīmējiet piekrišanu, citādi iesniegumu nevaram reģistrēt.",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def status_class(statuss: str) -> str:
    return {"Jauns": "jauns", "Apstrādē": "apstrade", "Atbildēts": "atbildets", "Noraidīts": "noraidits"}[statuss]


def fmt_date(value: str | None, with_time: bool = False) -> str:
    if not value:
        return "—"
    d = datetime.fromisoformat(value)
    return d.strftime("%d.%m.%Y %H:%M" if with_time else "%d.%m.%Y")


def next_numurs(conn: sqlite3.Connection, year: int) -> str:
    row = conn.execute("SELECT MAX(numurs) FROM iesniegumi WHERE numurs LIKE ?", (f"{year}-%",)).fetchone()
    seq = int(row[0].split("-")[1]) + 1 if row[0] else 1
    return f"{year}-{seq:04d}"


def register_views(app: Flask) -> None:
    db = app.db
    app.jinja_env.globals.update(status_class=status_class, fmt_date=fmt_date, field_labels=FIELD_LABELS)

    def temas() -> list[sqlite3.Row]:
        return db().execute("SELECT id, nosaukums FROM temas ORDER BY id").fetchall()

    def get_iesniegums(numurs: str) -> sqlite3.Row | None:
        return db().execute(
            "SELECT i.*, t.nosaukums AS tema FROM iesniegumi i JOIN temas t ON t.id = i.tema_id WHERE i.numurs = ?",
            (numurs,),
        ).fetchone()

    def log_event(iesniegums_id: int, loma: str, veids: str, apraksts: str) -> None:
        db().execute(
            "INSERT INTO notikumi (iesniegums_id, laiks, loma, veids, apraksts) VALUES (?, ?, ?, ?, ?)",
            (iesniegums_id, now_iso(), loma, veids, apraksts),
        )

    app.get_iesniegums = get_iesniegums
    app.log_event = log_event
    app.temas = temas

    # --- US-1 · iesnieguma iesniegšana ------------------------------------------------

    @app.get("/iesniegt")
    def iesniegt():
        return render_template("iesniegt.html", temas=temas(), values={}, errors={})

    @app.post("/iesniegt")
    def iesniegt_post():
        values = {
            "vards": " ".join(request.form.get("vards", "").split()),
            "epasts": request.form.get("epasts", "").strip(),
            "tema": request.form.get("tema", ""),
            "vieta": " ".join(request.form.get("vieta", "").split()),
            "apraksts": request.form.get("apraksts", "").strip(),
            "piekrisana": request.form.get("piekrisana") == "1",
        }
        tema_ids = {str(t["id"]) for t in temas()}
        issues = []
        if not values["vards"]:
            issues.append(("vards", "REQUIRED"))
        elif not NAME_RE.fullmatch(values["vards"]) or len(values["vards"]) > 100:
            issues.append(("vards", "FORMAT"))
        if not values["epasts"]:
            issues.append(("epasts", "REQUIRED"))
        elif not EMAIL_RE.fullmatch(values["epasts"]) or len(values["epasts"]) > 254:
            issues.append(("epasts", "FORMAT"))
        if values["tema"] not in tema_ids:
            issues.append(("tema", "REQUIRED"))
        if not values["vieta"]:
            issues.append(("vieta", "REQUIRED"))
        if not values["apraksts"]:
            issues.append(("apraksts", "REQUIRED"))
        elif len(values["apraksts"]) > APRAKSTS_MAX:
            issues.append(("apraksts", "TOO_LONG"))
        if not values["piekrisana"]:
            issues.append(("piekrisana", "REQUIRED"))
        if issues:
            errors = {field: MESSAGES[(field, code)] for field, code in issues}
            return render_template("iesniegt.html", temas=temas(), values=values, errors=errors), 400

        conn = db()
        created = now_iso()
        for _ in range(5):  # vienlaicīgas iesniegšanas gadījumā mēģina nākamo numuru
            numurs = next_numurs(conn, datetime.now(timezone.utc).year)
            try:
                cur = conn.execute(
                    "INSERT INTO iesniegumi (numurs, izveidots, vards, epasts, tema_id, vieta, apraksts, piekrisana) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, 1)",
                    (numurs, created, values["vards"], values["epasts"], int(values["tema"]), values["vieta"], values["apraksts"]),
                )
                break
            except sqlite3.IntegrityError:
                continue
        else:
            abort(500)
        log_event(cur.lastrowid, "iedzivotajs", "iesniegts", "Iesniegums reģistrēts")
        conn.commit()
        # US-2: POST → redirect → GET, lai F5 neiesniegtu atkārtoti
        return redirect(url_for("iesniegts", numurs=numurs), code=303)

    # --- US-2 · apstiprinājums ----------------------------------------------------------

    @app.get("/iesniegts/<numurs>")
    def iesniegts(numurs: str):
        row = get_iesniegums(numurs)
        if row is None:
            abort(404)
        return render_template("iesniegts.html", numurs=row["numurs"], tema=row["tema"])

    # --- US-8 · mans iesniegums -------------------------------------------------------------

    @app.get("/mans-iesniegums")
    def mans_iesniegums():
        numurs = request.args.get("numurs", "").strip()
        if not numurs:
            return render_template("mans_iesniegums.html", numurs="", row=None, error=None, last=None)
        error = None
        row = None
        if not NUMURS_RE.fullmatch(numurs):
            error = f"Numurs «{numurs}» nav pareizā formā. Numurs izskatās šādi: 2026-0001 (gads, defise, četri cipari)."
        else:
            row = get_iesniegums(numurs)
            if row is None:
                error = f"Iesniegums ar numuru {numurs} nav atrasts. Pārbaudiet numuru apstiprinājuma lapā vai e-pastā."
        last = None
        if row is not None:
            # Iedzīvotājam rāda tikai publiskos notikumus (ne iekšējos komentārus un MI)
            last = db().execute(
                "SELECT laiks, apraksts FROM notikumi WHERE iesniegums_id = ? AND veids IN ('iesniegts', 'statuss') "
                "ORDER BY laiks DESC, id DESC LIMIT 1",
                (row["id"],),
            ).fetchone()
        return render_template("mans_iesniegums.html", numurs=numurs, row=row, error=error, last=last), (404 if error and not row else 200)

    # --- US-3 · iesniegumu saraksts ---------------------------------------------------

    STATUSI = ("Jauns", "Apstrādē", "Atbildēts", "Noraidīts")

    @app.get("/darbinieks/iesniegumi")
    def saraksts():
        app.require("darbinieks", "vaditajs")
        statuss = request.args.get("statuss", "")
        tema = request.args.get("tema", "")
        meklet = " ".join(request.args.get("q", "").split())
        where, params = ["1 = 1"], []
        if statuss in STATUSI:
            where.append("i.statuss = ?")
            params.append(statuss)
        if tema.isdigit():
            where.append("i.tema_id = ?")
            params.append(int(tema))
        if meklet:
            like = "%" + meklet.casefold().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
            where.append("(lv_lower(i.numurs) LIKE ? ESCAPE '\\' OR lv_lower(i.vards) LIKE ? ESCAPE '\\' "
                         "OR lv_lower(i.vieta) LIKE ? ESCAPE '\\' OR lv_lower(i.apraksts) LIKE ? ESCAPE '\\')")
            params += [like] * 4
        rows = db().execute(
            "SELECT i.numurs, i.izveidots, i.vards, i.statuss, t.nosaukums AS tema FROM iesniegumi i "
            f"JOIN temas t ON t.id = i.tema_id WHERE {' AND '.join(where)} ORDER BY i.izveidots DESC, i.id DESC",
            params,
        ).fetchall()
        filtered = bool(statuss or tema or meklet)
        return render_template("saraksts.html", rows=rows, temas=temas(), statusi=STATUSI,
                               statuss=statuss, tema=tema, q=meklet, filtered=filtered)

    # --- US-4 · detaļas un apstrāde, US-7 · MI ieteikums --------------------------------

    NEXT = {"Jauns": ("Apstrādē",), "Apstrādē": ("Atbildēts", "Noraidīts")}
    NOTICES = {
        "statuss": "Statuss nomainīts uz «{statuss}».",
        "projekts": "Atbildes melnraksts saglabāts. Iedzīvotājam tas nav nosūtīts.",
        "komentars": "Komentārs pievienots vēsturei.",
        "mi": "MI projekts ielikts atbildes laukā. Pārbaudiet un rediģējiet to pirms nosūtīšanas.",
        "mi_tema": "Tēma nomainīta uz MI ieteikto «{tema}».",
    }
    mi_cache: dict[tuple[int, str], tuple[dict, str]] = {}

    def mi_for(row) -> tuple[dict, str]:
        """Ieteikums tiek aprēķināts vienreiz katram aprakstam (Claude API netiek saukts katrā lapas atvēršanā)."""
        key = (row["id"], row["apraksts"])
        if key not in mi_cache:
            mi_cache[key] = ai.ieteikums_ar_avotu(row["apraksts"])
        return mi_cache[key]

    def detail(row, errors=None, values=None, status_code=200):
        events = db().execute(
            "SELECT laiks, loma, veids, apraksts FROM notikumi WHERE iesniegums_id = ? ORDER BY laiks, id", (row["id"],)
        ).fetchall()
        mi, mi_avots = mi_for(row)
        notice_key = request.args.get("pazinojums", "")
        notice = NOTICES.get(notice_key, "").format(statuss=row["statuss"], tema=row["tema"]) if notice_key else ""
        return render_template(
            "detalas.html", row=row, events=events, next_statuses=NEXT.get(row["statuss"], ()), mi=mi, mi_avots=mi_avots,
            notice=notice, errors=errors or {}, values=values or {}, lomas_nosaukumi={**LOMAS_EVENT},
        ), status_code

    LOMAS_EVENT = {"iedzivotajs": "Iedzīvotājs", "darbinieks": "Darbinieks", "vaditajs": "Vadītājs", "sistema": "Sistēma"}

    def load(numurs: str):
        loma = app.require("darbinieks", "vaditajs")
        row = get_iesniegums(numurs)
        if row is None:
            abort(404)
        return loma, row

    def back(numurs: str, key: str):
        return redirect(url_for("detalas", numurs=numurs, pazinojums=key) + "#pazinojums", code=303)

    @app.get("/darbinieks/iesniegumi/<numurs>")
    def detalas(numurs: str):
        _, row = load(numurs)
        return detail(row)

    @app.post("/darbinieks/iesniegumi/<numurs>/statuss")
    def mainit_statusu(numurs: str):
        loma, row = load(numurs)
        target = request.form.get("statuss", "")
        if target not in NEXT.get(row["statuss"], ()):
            abort(400)
        atbilde = request.form.get("atbilde", "").strip()
        if target in ("Atbildēts", "Noraidīts") and not atbilde:
            msg = ("Ierakstiet atbildi iedzīvotājam, pirms maināt statusu uz «Atbildēts»." if target == "Atbildēts"
                   else "Ierakstiet noraidījuma pamatojumu, pirms maināt statusu uz «Noraidīts».")
            return detail(row, errors={"atbilde": msg}, values={"atbilde": atbilde}, status_code=400)
        conn = db()
        if target in ("Atbildēts", "Noraidīts"):
            conn.execute("UPDATE iesniegumi SET statuss = ?, atbilde = ?, atbildes_projekts = NULL, slegts = ? WHERE id = ?",
                         (target, atbilde, now_iso(), row["id"]))
        else:
            conn.execute("UPDATE iesniegumi SET statuss = ? WHERE id = ?", (target, row["id"]))
        log_event(row["id"], loma, "statuss", f"Statuss: {row['statuss']} → {target}")
        conn.commit()
        return back(numurs, "statuss")

    @app.post("/darbinieks/iesniegumi/<numurs>/projekts")
    def saglabat_projektu(numurs: str):
        _, row = load(numurs)
        if row["statuss"] not in NEXT:
            abort(400)
        db().execute("UPDATE iesniegumi SET atbildes_projekts = ? WHERE id = ?", (request.form.get("atbilde", "").strip(), row["id"]))
        db().commit()
        return back(numurs, "projekts")

    @app.post("/darbinieks/iesniegumi/<numurs>/komentars")
    def pievienot_komentaru(numurs: str):
        loma, row = load(numurs)
        komentars = " ".join(request.form.get("komentars", "").split())
        if not komentars:
            return detail(row, errors={"komentars": "Ierakstiet komentāra tekstu."}, status_code=400)
        log_event(row["id"], loma, "komentars", f"Komentārs: {komentars[:1000]}")
        db().commit()
        return back(numurs, "komentars")

    @app.post("/darbinieks/iesniegumi/<numurs>/mi-izmantot")
    def mi_izmantot(numurs: str):
        """US-7: projekts nonāk atbildes laukā rediģēšanai; nekas netiek nosūtīts, statuss nemainās."""
        loma, row = load(numurs)
        if row["statuss"] not in NEXT:
            abort(400)
        mi, avots = mi_for(row)
        db().execute("UPDATE iesniegumi SET atbildes_projekts = ? WHERE id = ?", (mi["atbildes_projekts"], row["id"]))
        log_event(row["id"], loma, "mi_izmantots", f"MI ieteikums ({avots}) izmantots: projekts ielikts atbildes laukā")
        db().commit()
        return back(numurs, "mi")

    @app.post("/darbinieks/iesniegumi/<numurs>/mi-tema")
    def mi_tema(numurs: str):
        loma, row = load(numurs)
        mi, avots = mi_for(row)
        tema = db().execute("SELECT id FROM temas WHERE nosaukums = ?", (mi["tema"],)).fetchone()
        if row["statuss"] not in NEXT or tema is None or mi["tema"] == row["tema"]:
            abort(400)
        db().execute("UPDATE iesniegumi SET tema_id = ? WHERE id = ?", (tema["id"], row["id"]))
        log_event(row["id"], loma, "mi_tema", f"Tēma mainīta pēc MI ieteikuma ({avots}): {row['tema']} → {mi['tema']}")
        db().commit()
        return back(numurs, "mi_tema")

    # --- US-5 · pārskats vadītājam ------------------------------------------------------

    @app.get("/vaditajs/parskats")
    def parskats():
        app.require("vaditajs")
        conn = db()
        by_status = [{"label": st, "n": conn.execute("SELECT COUNT(*) FROM iesniegumi WHERE statuss = ?", (st,)).fetchone()[0]}
                     for st in STATUSI]
        by_topic = [dict(r) for r in conn.execute(
            "SELECT t.nosaukums AS label, COUNT(i.id) AS n FROM temas t LEFT JOIN iesniegumi i ON i.tema_id = t.id "
            "GROUP BY t.id ORDER BY t.id").fetchall()]
        closed = conn.execute("SELECT izveidots, slegts FROM iesniegumi WHERE slegts IS NOT NULL").fetchall()
        days = [(datetime.fromisoformat(r["slegts"]) - datetime.fromisoformat(r["izveidots"])).total_seconds() / 86400 for r in closed]
        avg_days = round(sum(days) / len(days), 1) if days else None
        total = sum(r["n"] for r in by_status)
        return render_template("parskats.html", by_status=by_status, by_topic=by_topic, avg_days=avg_days,
                               closed=len(days), total=total, chart=bar_chart(by_topic))

    # --- US-6 · piekļūstamības paziņojums ---------------------------------------------------

    @app.get("/pieklustamiba")
    def pieklustamiba():
        report_path = Path(app.root_path) / "a11y-report.json"
        try:
            report = json.loads(report_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            report = None
        return render_template("pieklustamiba.html", report=report)


# --- US-5 diagramma: horizontāla joslu diagramma inline SVG (bez JS) ---------------------

CHART = {"width": 640, "label_w": 170, "value_w": 40, "row_h": 32, "bar_h": 20, "top": 6, "axis_h": 24}


def nice_step(max_value: int) -> int:
    if max_value <= 5:
        return 1
    raw = max_value / 5
    mag = 10 ** math.floor(math.log10(raw))
    return next(m * mag for m in (1, 2, 5, 10) if m * mag >= raw)


def bar_chart(rows: list[dict]) -> dict:
    c = CHART
    top = max((r["n"] for r in rows), default=0)
    step = nice_step(top)
    axis_max = max(step, math.ceil(top / step) * step)
    plot_w = c["width"] - c["label_w"] - c["value_w"]
    bars = []
    for i, r in enumerate(rows):
        y = c["top"] + i * c["row_h"]
        w = r["n"] * plot_w / axis_max
        by = y + (c["row_h"] - c["bar_h"]) / 2
        x, h, rad = c["label_w"], c["bar_h"], min(4, w, c["bar_h"] / 2)
        path = "" if w <= 0 else (f"M{x},{by} H{x + w - rad:.1f} Q{x + w:.1f},{by} {x + w:.1f},{by + rad:.1f} "
                                   f"V{by + h - rad:.1f} Q{x + w:.1f},{by + h} {x + w - rad:.1f},{by + h} H{x} Z")
        bars.append({"label": r["label"], "value": r["n"], "y": y, "w": w, "path": path})
    plot_bottom = c["top"] + len(rows) * c["row_h"]
    ticks = [{"value": v, "x": c["label_w"] + v * plot_w / axis_max} for v in range(0, axis_max + 1, step)]
    return {**c, "bars": bars, "ticks": ticks, "plot_bottom": plot_bottom, "height": plot_bottom + c["axis_h"]}
