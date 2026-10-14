"""«Iesniegumi» · Ezermalas novada pašvaldības iesniegumu sistēma (mācību prototips).

Flask + Jinja2 + SQLite, servera pusē renderēts HTML. Palaišana: `python app.py` → http://localhost:8001
"""

from __future__ import annotations

import os
import secrets
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, abort, g, redirect, render_template, request, session, url_for

import seed

HERE = Path(__file__).resolve().parent
LOMAS = {"iedzivotajs": "Iedzīvotājs", "darbinieks": "Darbinieks", "vaditajs": "Vadītājs"}
DARBINIEKU_LOMAS = ("darbinieks", "vaditajs")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def init_db(path: Path, with_seed: bool = True) -> None:
    """S0.2: shēma no schema.sql un testa dati."""
    conn = sqlite3.connect(path)
    conn.executescript((HERE / "schema.sql").read_text(encoding="utf-8"))
    if with_seed:
        seed.seed(conn)
    conn.close()


def create_app(db_path: Path | str | None = None) -> Flask:
    db_path = Path(db_path or os.environ.get("IESN_DB", HERE / "data.db"))
    init_db(db_path)

    app = Flask(__name__)
    app.secret_key = os.environ.get("IESN_SECRET_KEY") or secrets.token_hex(32)
    app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax", DB_PATH=db_path)

    # --- Datubāze ------------------------------------------------------------------

    def db() -> sqlite3.Connection:
        if "db" not in g:
            g.db = sqlite3.connect(db_path)
            g.db.row_factory = sqlite3.Row
            g.db.execute("PRAGMA foreign_keys = ON")
            # SQLite LOWER() strādā tikai ar ASCII; latviešu burtiem vajag Python casefold (US-3 meklēšana)
            g.db.create_function("lv_lower", 1, lambda v: v.casefold() if isinstance(v, str) else v, deterministic=True)
        return g.db

    @app.teardown_appcontext
    def close_db(_exc):
        conn = g.pop("db", None)
        if conn is not None:
            conn.close()

    app.db = db  # testiem un citiem moduļiem

    # --- Lomas (mācību režīms: izvēle bez paroles) -----------------------------------

    def loma() -> str | None:
        return session.get("loma")

    def require(*roles: str) -> str:
        current = loma()
        if current is None:
            abort(redirect(url_for("sakums", vajag="loma"), code=303))
        if current not in roles:
            abort(403)
        return current

    app.require = require

    @app.context_processor
    def globals_for_templates():
        return {"loma": loma(), "lomas": LOMAS, "endpoints": app.view_functions}

    @app.errorhandler(403)
    def forbidden(_e):
        return render_template("kluda.html", kods=403), 403

    @app.errorhandler(404)
    def not_found(_e):
        return render_template("kluda.html", kods=404), 404

    # --- Ekrāns 1 · sākumlapa: lomas izvēle ---------------------------------------------

    @app.get("/")
    def sakums():
        return render_template("sakums.html", vajag_lomu=request.args.get("vajag") == "loma")

    @app.post("/loma")
    def izvelas_lomu():
        izvele = request.form.get("loma", "")
        if izvele not in LOMAS:
            return render_template("sakums.html", kluda="Izvēlieties vienu no lomām."), 400
        session["loma"] = izvele
        return redirect({"iedzivotajs": url_for("iesniegt"), "darbinieks": url_for("saraksts"),
                         "vaditajs": url_for("parskats")}[izvele], code=303)

    @app.post("/iziet")
    def iziet():
        session.pop("loma", None)
        return redirect(url_for("sakums"), code=303)

    from views import register_views  # noqa: E402 — ekrāni 2–8 atsevišķā modulī
    register_views(app)
    return app


if __name__ == "__main__":
    create_app().run(host="0.0.0.0", port=int(os.environ.get("PORT", 8001)), debug=False)
