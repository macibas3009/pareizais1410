"""Ekrāni 2–8. Katra US maršruti savā sadaļā."""

from __future__ import annotations

import re
import sqlite3
from datetime import datetime, timezone

from flask import Flask, abort, redirect, render_template, request, url_for

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

    # --- Vietturi nākamajiem US -------------------------------------------------------

    @app.get("/darbinieks/iesniegumi")
    def saraksts():
        app.require("darbinieks", "vaditajs")
        return "US-3", 200

    @app.get("/vaditajs/parskats")
    def parskats():
        app.require("vaditajs")
        return "US-5", 200
