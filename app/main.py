"""Ezermalas pieteikumu sistēma · CRM (Flask + Jinja2 + SQLite, N4).

Palaišana: `make run`, tad atver http://localhost:8000/login
"""

from __future__ import annotations

import logging
import os
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from flask import Flask, g, jsonify, redirect, render_template, request
from werkzeug.exceptions import HTTPException

from app import accounts, dashboard, db

VERSION = "0.1.0"
API_PREFIXES = ("/auth/", "/health")

# Kļūdu teksti reģistrācijas formā (N1: pie lauka un kopsavilkumā)
FIELD_LABELS = {"fullName": "Vārds, uzvārds", "email": "E-pasts", "password": "Parole", "password2": "Parole vēlreiz"}
ISSUE_MESSAGES = {
    ("fullName", "REQUIRED"): "Ievadiet vārdu un uzvārdu.",
    ("fullName", "INVALID_FORMAT"): "Vārdā drīkst būt tikai burti, atstarpes, defise un apostrofs.",
    ("email", "REQUIRED"): "Ievadiet e-pasta adresi.",
    ("email", "INVALID_FORMAT"): "Ievadiet derīgu e-pasta adresi, piemēram, vards@example.com.",
    ("email", "TAKEN"): "Šis e-pasts jau ir reģistrēts.",
    ("password", "REQUIRED"): "Ievadiet paroli.",
    ("password", "TOO_SHORT"): f"Parolei jābūt vismaz {accounts.PASSWORD_MIN} rakstzīmes garai.",
    ("password", "TOO_LONG"): f"Parole nedrīkst būt garāka par {accounts.PASSWORD_MAX} rakstzīmēm.",
    ("password2", "MISMATCH"): "Paroles nesakrīt.",
}

log = logging.getLogger("app")


def api_error(status: int, code: str, message: str, details: list[dict] | None = None):
    """Vienotā Error shēma (docs/openapi.yaml)."""
    body: dict[str, Any] = {"code": code, "message": message}
    if details:
        body["details"] = details
    return jsonify({"error": body}), status


def wants_json() -> bool:
    return request.path.startswith(API_PREFIXES) or "text/html" not in request.headers.get("Accept", "")


def create_app(db_path: Path | None = None, cookie_secure: bool | None = None) -> Flask:
    db_path = Path(db_path or os.environ.get("APP_DB_PATH", "data/app.db"))
    if cookie_secure is None:
        cookie_secure = os.environ.get("COOKIE_SECURE", "0") == "1"

    db.connect(db_path).close()

    app = Flask(__name__)
    app.jinja_env.globals.update(
        fmt_date=dashboard.fmt_date,
        long_date=dashboard.long_date,
        due_label=dashboard.due_label,
        first_sentence=dashboard.first_sentence,
        plural=dashboard.plural,
        field_labels=FIELD_LABELS,
        password_min=accounts.PASSWORD_MIN,
        role_label=lambda role: dashboard.ROLE_LABELS.get(role or "", "Gaida apstiprinājumu"),
    )

    # --- Datubāze un pašreizējais lietotājs -----------------------------------

    def conn():
        if "db" not in g:
            g.db = db.open_db(db_path)
        return g.db

    @app.teardown_appcontext
    def close_db(_exc):
        connection = g.pop("db", None)
        if connection is not None:
            connection.close()

    def current_user():
        if "user" not in g:
            # Loma tiek nolasīta no datubāzes katrā pieprasījumā (N3)
            g.user = accounts.user_by_session(conn(), request.cookies.get(accounts.SESSION_COOKIE))
        return g.user

    def start_session(response, user_id: int):
        response.set_cookie(
            accounts.SESSION_COOKIE,
            accounts.create_session(conn(), user_id),
            max_age=int(accounts.SESSION_TTL.total_seconds()),
            httponly=True,
            samesite="Lax",
            secure=cookie_secure,
        )
        return response

    def finish_session(response):
        accounts.end_session(conn(), request.cookies.get(accounts.SESSION_COOKIE))
        response.delete_cookie(accounts.SESSION_COOKIE)
        return response

    # --- Kļūdas ---------------------------------------------------------------

    @app.errorhandler(HTTPException)
    def on_http_error(exc: HTTPException):
        if wants_json():
            code = "NOT_FOUND" if exc.code == 404 else "HTTP_ERROR"
            message = "Resource not found" if exc.code == 404 else (exc.name or "HTTP error")
            return api_error(exc.code or 500, code, message)
        return render_template("error.html", status=exc.code, user=current_user()), exc.code

    @app.errorhandler(Exception)
    def on_unexpected(exc: Exception):
        # Tikai kļūdas tips, nekad pieprasījuma saturs (F0, N2)
        log.error("Unhandled error: %s", type(exc).__name__)
        if wants_json():
            return api_error(500, "INTERNAL_ERROR", "Internal server error")
        return render_template("error.html", status=500, user=None), 500

    # --- F0 · pieslēgšanās un reģistrācija (HTML formas, bez JavaScript) ------

    @app.get("/")
    def index():
        return redirect("/panelis" if current_user() else "/login")

    @app.get("/login")
    def login_page():
        if current_user():
            return redirect("/panelis")
        return render_template("login.html", registered="registered" in request.args, email="")

    @app.post("/login")
    def login_submit():
        email = request.form.get("email", "")
        password = request.form.get("password", "")
        if not email.strip() or not password:
            return render_template("login.html", error="Ievadiet e-pastu un paroli.", email=email), 400
        user = accounts.authenticate(conn(), email, password)
        if user is None:
            log.warning("Failed login attempt")
            return render_template("login.html", error="Nepareizs e-pasts vai parole.", email=email), 401
        return start_session(redirect("/panelis", code=303), user["id"])

    @app.get("/register")
    def register_page():
        return render_template("register.html", errors={}, values={})

    @app.post("/register")
    def register_submit():
        values = {
            "fullName": request.form.get("fullName", "").strip(),
            "email": accounts.normalize_email(request.form.get("email", "")),
        }
        password = request.form.get("password", "")
        details = accounts.validate_registration(values["email"], values["fullName"], password)
        if password and password != request.form.get("password2", ""):
            details.append({"field": "password2", "issue": "MISMATCH"})

        status = 400
        if not details:
            if accounts.register(conn(), values["email"], values["fullName"], password) is not None:
                return redirect("/login?registered=1", code=303)
            details = [{"field": "email", "issue": "TAKEN"}]
            status = 409

        errors = {d["field"]: ISSUE_MESSAGES[(d["field"], d["issue"])] for d in details}
        return render_template("register.html", errors=errors, values=values), status

    @app.post("/iziet")
    def logout_form():
        return finish_session(redirect("/login", code=303))

    @app.get("/profile")
    def profile_page():
        return redirect("/panelis")

    # --- F9 · vadības panelis -------------------------------------------------

    @app.get("/panelis")
    def dashboard_page():
        user = current_user()
        if user is None:
            return redirect("/login", code=303)
        return render_template("panelis.html", user=user, today=date.today(), **dashboard.context(conn(), user, date.today()))

    @app.post("/uzdevumi/<int:task_id>/izpildits")
    def complete_task(task_id: int):
        user = current_user()
        if user is None:
            return redirect("/login", code=303)
        if user["role"] not in ("darbinieks", "vaditajs"):
            return api_error(403, "FORBIDDEN", "Not allowed")
        if not dashboard.complete_task(conn(), task_id, user, datetime.now(timezone.utc).isoformat()):
            return api_error(404, "NOT_FOUND", "Task not found")
        return redirect("/panelis", code=303)

    # --- JSON API (docs/openapi.yaml) -----------------------------------------

    @app.get("/health")
    def health():
        return {"status": "ok", "version": VERSION}

    def json_fields(*names: str) -> tuple[dict[str, str], list[dict]]:
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            return {}, [{"field": "body", "issue": "INVALID_FORMAT"}]
        values, details = {}, []
        for name in names:
            if name not in payload:
                details.append({"field": name, "issue": "REQUIRED"})
            elif not isinstance(payload[name], str):
                details.append({"field": name, "issue": "INVALID_FORMAT"})
            else:
                values[name] = payload[name]
        return values, details

    @app.post("/auth/register")
    def api_register():
        values, details = json_fields("email", "fullName", "password")
        if details:
            return api_error(400, "VALIDATION_ERROR", "Request validation failed", details)
        email = accounts.normalize_email(values["email"])
        full_name = values["fullName"].strip()
        details = accounts.validate_registration(email, full_name, values["password"])
        if details:
            return api_error(400, "VALIDATION_ERROR", "Request validation failed", details)
        user_id = accounts.register(conn(), email, full_name, values["password"])
        if user_id is None:
            return api_error(409, "EMAIL_TAKEN", "Email is already registered")
        log.info("User registered: id=%s", user_id)
        return {"id": user_id, "email": email, "fullName": full_name}, 201

    @app.post("/auth/login")
    def api_login():
        values, details = json_fields("email", "password")
        if details:
            return api_error(400, "VALIDATION_ERROR", "Request validation failed", details)
        user = accounts.authenticate(conn(), values["email"], values["password"])
        if user is None:
            log.warning("Failed login attempt")
            return api_error(401, "INVALID_CREDENTIALS", "Invalid email or password")
        return start_session(jsonify(accounts.user_out(user)), user["id"])

    @app.post("/auth/logout")
    def api_logout():
        return finish_session(app.response_class(status=204))

    @app.get("/auth/me")
    def api_me():
        user = current_user()
        if user is None:
            return api_error(401, "UNAUTHENTICATED", "Not logged in")
        return accounts.user_out(user)

    return app
