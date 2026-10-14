"""Ezermalas pieteikumu sistēma · CRM (Flask + Jinja2 + SQLite, N4).

Palaišana: `make run`, tad atver http://localhost:8000/login
"""

from __future__ import annotations

import json
import logging
import os
from datetime import date
from pathlib import Path
from typing import Any

from flask import Flask, abort, g, jsonify, redirect, render_template, request
from werkzeug.exceptions import HTTPException

from app import accounts, ai, audit, contacts, dashboard, db, interactions, org_requests, organizations, report, search, tasks, users

VERSION = "0.1.0"
API_PREFIXES = ("/auth/", "/health")

# Kļūdu teksti reģistrācijas formā (N1: pie lauka un kopsavilkumā)
FIELD_LABELS = {
    "fullName": "Vārds, uzvārds",
    "email": "E-pasts",
    "requested_role": "Pieprasītā loma",
    "password": "Parole",
    "password2": "Parole vēlreiz",
}
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
    ("requested_role", "REQUIRED"): "Izvēlieties, kādu lomu pieprasāt.",
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
        role_labels=dashboard.ROLE_LABELS,
        requestable_roles=db.REQUESTABLE_ROLES,
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
        if exc.response is not None:  # abort(redirect(...)) no require()
            return exc.response
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
            "requested_role": request.form.get("requested_role", ""),
        }
        password = request.form.get("password", "")
        details = accounts.validate_registration(values["email"], values["fullName"], password)
        if values["requested_role"] not in db.REQUESTABLE_ROLES:
            details.append({"field": "requested_role", "issue": "REQUIRED"})
        if password and password != request.form.get("password2", ""):
            details.append({"field": "password2", "issue": "MISMATCH"})

        status = 400
        if not details:
            user_id = accounts.register(conn(), values["email"], values["fullName"], password, values["requested_role"])
            if user_id is not None:
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
        if not tasks.complete(conn(), task_id, user):
            return api_error(404, "NOT_FOUND", "Task not found")
        back = request.form.get("atpakal", "")
        return redirect(back if back in ("/uzdevumi", "/panelis") or back.startswith("/pieprasijumi/") else "/panelis", code=303)

    # --- Lomu pārbaude (N3) ---------------------------------------------------

    def require(*roles: str):
        """Atgriež pieslēgto lietotāju ar atļautu lomu; citādi novirza uz /login vai 403."""
        user = current_user()
        if user is None:
            abort(redirect("/login", code=303))
        if user["role"] not in roles:
            abort(403)
        return user

    # --- F0 #6 · lomu apstiprināšana (administrators) --------------------------

    @app.get("/lietotaji")
    def users_page():
        admin = require("administrators")
        return render_template("lietotaji.html", user=admin, people=users.all_users(conn()),
                               message=request.args.get("zinojums"), error=None)

    @app.post("/lietotaji/<int:user_id>/loma")
    def users_set_role(user_id: int):
        admin = require("administrators")
        problem = users.set_role(conn(), admin, user_id, request.form.get("role", ""))
        if problem:
            return render_template("lietotaji.html", user=admin, people=users.all_users(conn()),
                                   message=None, error=problem), 400
        back = "/panelis" if request.form.get("back") == "panelis" else "/lietotaji?zinojums=saglabats"
        return redirect(back, code=303)

    @app.post("/lietotaji/<int:user_id>/noraidit")
    def users_reject(user_id: int):
        admin = require("administrators")
        problem = users.reject(conn(), admin, user_id)
        if problem:
            return render_template("lietotaji.html", user=admin, people=users.all_users(conn()),
                                   message=None, error=problem), 400
        return redirect("/panelis", code=303)

    @app.get("/zurnals")
    def access_log_page():
        admin = require("administrators")
        return render_template("zurnals.html", user=admin, entries=audit.recent(conn()),
                               action_labels=audit.ACTION_LABELS, object_labels=audit.OBJECT_LABELS)

    # --- F1 · organizācijas -----------------------------------------------------

    CRM_ROLES = ("darbinieks", "vaditajs")

    def org_form(user, org=None, values=None, details=(), status=200):
        errors = {d["field"]: organizations.MESSAGES[(d["field"], d["issue"])] for d in details}
        return render_template(
            "organizacija_forma.html", user=user, org=org, values=values or {}, errors=errors,
            labels=organizations.FIELD_LABELS,
            kinds_options=[(k, k) for k in organizations.KINDS],
            staff_options=[(s["id"], s["full_name"]) for s in users.staff(conn())],
        ), status

    @app.get("/organizacijas")
    def organizations_page():
        user = require(*CRM_ROLES)
        kind = request.args.get("veids", "")
        responsible = request.args.get("atbildigais", "")
        responsible_id = user["id"] if responsible == "mani" else (int(responsible) if responsible.isdigit() else None)
        return render_template(
            "organizacijas.html", user=user, kinds=organizations.KINDS, staff=users.staff(conn()),
            rows=organizations.list_all(conn(), kind or None, responsible_id),
            kind=kind, responsible=responsible, created=request.args.get("izveidota"),
        )

    @app.get("/organizacijas/jauna")
    def organization_new():
        user = require(*CRM_ROLES)
        return org_form(user, values={"responsible_id": user["id"]})

    @app.post("/organizacijas/jauna")
    def organization_create():
        user = require(*CRM_ROLES)
        values = organizations.read_form(request.form, user)
        staff_ids = {s["id"] for s in users.staff(conn())}
        details = organizations.validate(conn(), values, staff_ids)
        if details:
            return org_form(user, values=values, details=details, status=400)
        org_id = organizations.create(conn(), values)
        audit.log(conn(), user["id"], "create", "organization", org_id)
        return redirect(f"/organizacijas/{org_id}?saglabats=1", code=303)

    @app.get("/organizacijas/<int:org_id>")
    def organization_card(org_id: int):
        user = require(*CRM_ROLES)
        org = organizations.get(conn(), org_id)
        if org is None:
            abort(404)
        # N2: katra kartītes atvēršana tiek ierakstīta žurnālā
        audit.log(conn(), user["id"], "view", "organization", org_id)
        return render_template(
            "organizacija.html", user=user, org=org, can_edit=organizations.can_edit(user, org),
            saved="saglabats" in request.args, interaction_saved="mijiedarbiba" in request.args,
            today=date.today(), **organizations.card(conn(), org_id),
        )

    @app.get("/organizacijas/<int:org_id>/labot")
    def organization_edit(org_id: int):
        user = require(*CRM_ROLES)
        org = organizations.get(conn(), org_id)
        if org is None:
            abort(404)
        if not organizations.can_edit(user, org):
            abort(403)
        return org_form(user, org=org, values=dict(org))

    @app.post("/organizacijas/<int:org_id>/labot")
    def organization_update(org_id: int):
        user = require(*CRM_ROLES)
        org = organizations.get(conn(), org_id)
        if org is None:
            abort(404)
        if not organizations.can_edit(user, org):
            abort(403)
        values = organizations.read_form(request.form, user, current_responsible=org["responsible_id"])
        staff_ids = {s["id"] for s in users.staff(conn())}
        details = organizations.validate(conn(), values, staff_ids, org_id=org_id)
        if details:
            return org_form(user, org=org, values=values, details=details, status=400)
        organizations.update(conn(), org_id, values)
        audit.log(conn(), user["id"], "update", "organization", org_id)
        return redirect(f"/organizacijas/{org_id}?saglabats=1", code=303)

    # --- F2 · kontaktpersonas, N2 · pārskatīšana un dzēšana --------------------

    def contact_form(user, org, contact=None, values=None, details=(), status=200):
        errors = {d["field"]: contacts.MESSAGES[(d["field"], d["issue"])] for d in details}
        return render_template(
            "kontakts_forma.html", user=user, org=org, contact=contact, values=values or {}, errors=errors,
            labels=contacts.FIELD_LABELS, today=date.today(), legal_basis=contacts.LEGAL_BASIS,
        ), status

    def editable_org(user, org_id: int):
        org = organizations.get(conn(), org_id)
        if org is None:
            abort(404)
        if not organizations.can_edit(user, org):
            abort(403)
        return org

    def editable_contact(user, contact_id: int):
        contact = contacts.get(conn(), contact_id)
        if contact is None:
            abort(404)
        if not contacts.can_edit(user, contact):
            abort(403)
        return contact

    @app.get("/organizacijas/<int:org_id>/kontakti/jauns")
    def contact_new(org_id: int):
        user = require(*CRM_ROLES)
        return contact_form(user, editable_org(user, org_id))

    @app.post("/organizacijas/<int:org_id>/kontakti/jauns")
    def contact_create(org_id: int):
        user = require(*CRM_ROLES)
        org = editable_org(user, org_id)
        values = contacts.read_form(request.form)
        details = contacts.validate(values, date.today())
        if details:
            return contact_form(user, org, values=values, details=details, status=400)
        contact_id = contacts.create(conn(), user, org_id, values, date.today())
        return redirect(f"/kontakti/{contact_id}?saglabats=1", code=303)

    @app.get("/kontakti/<int:contact_id>")
    def contact_card(contact_id: int):
        user = require(*CRM_ROLES)
        contact = contacts.get(conn(), contact_id)
        if contact is None:
            abort(404)
        # N2: katra kontaktpersonas kartītes atvēršana tiek ierakstīta žurnālā
        audit.log(conn(), user["id"], "view", "contact", contact_id)
        return render_template(
            "kontakts.html", user=user, contact=contact, can_edit=contacts.can_edit(user, contact),
            today=date.today(), pending_deletion=contacts.open_deletion_request(conn(), contact_id),
            notice=request.args.get("zinojums"), saved="saglabats" in request.args, error=None,
        )

    @app.get("/kontakti/<int:contact_id>/labot")
    def contact_edit(contact_id: int):
        user = require(*CRM_ROLES)
        contact = editable_contact(user, contact_id)
        values = dict(contact)
        values["email"] = values["email"] or ""
        values["phone"] = values["phone"] or ""
        return contact_form(user, organizations.get(conn(), contact["organization_id"]), contact, values)

    @app.post("/kontakti/<int:contact_id>/labot")
    def contact_update(contact_id: int):
        user = require(*CRM_ROLES)
        contact = editable_contact(user, contact_id)
        values = contacts.read_form(request.form)
        details = contacts.validate(values, date.today())
        if details:
            org = organizations.get(conn(), contact["organization_id"])
            return contact_form(user, org, contact, values, details, status=400)
        contacts.update(conn(), user, contact_id, values)
        return redirect(f"/kontakti/{contact_id}?saglabats=1", code=303)

    @app.get("/kontakti/japarskata")
    def contacts_review():
        user = require(*CRM_ROLES)
        return render_template("japarskata.html", user=user, rows=contacts.to_review(conn(), user, date.today()),
                               notice=request.args.get("zinojums"), today=date.today())

    @app.post("/kontakti/<int:contact_id>/pagarinat")
    def contact_extend(contact_id: int):
        user = require(*CRM_ROLES)
        editable_contact(user, contact_id)
        problem = contacts.extend(conn(), user, contact_id, request.form.get("reason", ""), date.today())
        if problem:
            rows = contacts.to_review(conn(), user, date.today())
            return render_template("japarskata.html", user=user, rows=rows, error=problem, error_id=contact_id,
                                   reason=request.form.get("reason", ""), notice=None, today=date.today()), 400
        return redirect("/kontakti/japarskata?zinojums=pagarinats", code=303)

    @app.get("/kontakti/<int:contact_id>/dzest")
    def contact_delete_confirm(contact_id: int):
        """Apstiprinājums pirms neatgriezeniskas dzēšanas (bez JavaScript)."""
        user = require(*CRM_ROLES)
        contact = editable_contact(user, contact_id)
        if contact["retain_until"] >= date.today().isoformat():
            abort(403)
        return render_template("apstiprinat_dzesanu.html", user=user, name=contact["full_name"],
                               organization=contact["organization"], action=f"/kontakti/{contact_id}/dzest",
                               back="/kontakti/japarskata")

    @app.post("/kontakti/<int:contact_id>/dzest")
    def contact_delete_expired(contact_id: int):
        """Dzēšana no saraksta "Jāpārskata": tikai, ja glabāšanas termiņš ir beidzies (N2)."""
        user = require(*CRM_ROLES)
        contact = editable_contact(user, contact_id)
        if contact["retain_until"] >= date.today().isoformat():
            abort(403)
        contacts.delete(conn(), user, contact_id)
        return redirect("/kontakti/japarskata?zinojums=dzests", code=303)

    @app.post("/kontakti/<int:contact_id>/dzesanas-pieprasijums")
    def contact_request_deletion(contact_id: int):
        user = require(*CRM_ROLES)
        contact = editable_contact(user, contact_id)
        contacts.request_deletion(conn(), user, contact)
        return redirect(f"/kontakti/{contact_id}?zinojums=dzesana", code=303)

    @app.get("/dzesanas-pieprasijumi")
    def deletion_requests_page():
        admin = require("administrators")
        return render_template("dzesanas_pieprasijumi.html", user=admin, rows=contacts.deletion_requests(conn()),
                               notice=request.args.get("zinojums"))

    @app.get("/dzesanas-pieprasijumi/<int:request_id>/izpildit")
    def deletion_request_confirm(request_id: int):
        admin = require("administrators")
        row = next((r for r in contacts.deletion_requests(conn()) if r["id"] == request_id and r["status"] == "open"), None)
        if row is None:
            abort(404)
        return render_template("apstiprinat_dzesanu.html", user=admin, name=row["contact"] or "Dzēsta kontaktpersona",
                               organization=row["organization"], action=f"/dzesanas-pieprasijumi/{request_id}/izpildit",
                               back="/dzesanas-pieprasijumi")

    @app.post("/dzesanas-pieprasijumi/<int:request_id>/<action>")
    def deletion_request_handle(request_id: int, action: str):
        admin = require("administrators")
        if action not in ("izpildit", "noraidit"):
            abort(404)
        if not contacts.handle_deletion_request(conn(), admin, request_id, approve=action == "izpildit"):
            abort(404)
        return redirect(f"/dzesanas-pieprasijumi?zinojums={action}", code=303)

    # --- F3 · mijiedarbības, MI-1 · kopsavilkums --------------------------------

    def interaction_form(user, org, values, details=(), status=200, ai_notice=None, ai_copy=False, ai_no_step=False):
        errors = {d["field"]: interactions.MESSAGES[(d["field"], d["issue"])] for d in details}
        org_contacts, staff = interactions.options(conn(), org["id"])
        return render_template(
            "mijiedarbiba_forma.html", user=user, org=org, values=values, errors=errors,
            labels=interactions.FIELD_LABELS, kinds=interactions.KINDS, org_contacts=org_contacts, staff=staff,
            today=date.today(), claude_enabled=ai.claude_enabled(), ai_notice=ai_notice,
            ai_copy=ai_copy, ai_no_step=ai_no_step,
        ), status

    def visible_org(org_id: int):
        org = organizations.get(conn(), org_id)
        if org is None:
            abort(404)
        return org

    @app.get("/organizacijas/<int:org_id>/mijiedarbibas/jauna")
    def interaction_new(org_id: int):
        user = require(*CRM_ROLES)
        values = {"date": date.today().isoformat(), "staff_ids": [user["id"]], "contact_ids": []}
        return interaction_form(user, visible_org(org_id), values)

    @app.post("/organizacijas/<int:org_id>/mijiedarbibas/jauna")
    def interaction_create(org_id: int):
        user = require(*CRM_ROLES)
        org = visible_org(org_id)
        values = interactions.read_form(request.form)

        if request.form.get("action") == "ai":
            # MI-1: kopsavilkums no brīvā teksta; darbinieks to pārbauda un apstiprina, saglabājot
            if not values["notes"].strip():
                return interaction_form(user, org, values, ai_notice="empty", status=400)
            result = ai.kopsavilkums(values["notes"])
            values.update(summary=result["kopsavilkums"], next_step=result["nakamais_solis"], ai_source=result["avots"])
            audit.log(conn(), user["id"], "ai_generate", "organization", org_id)
            # Godīgums par imitāciju: vai tā tiešām saīsināja piezīmes un atrada nākamo soli
            return interaction_form(
                user, org, values, ai_notice="generated",
                ai_copy=result["avots"] == "imitacija" and ai.parak_lidzigs(values["notes"], result["kopsavilkums"]),
                ai_no_step=result["nakamais_solis"] == ai.DEFAULT_NEXT_STEP,
            )

        org_contacts, staff = interactions.options(conn(), org_id)
        details = interactions.validate(values, {c["id"] for c in org_contacts}, {s["id"] for s in staff}, date.today())
        if details:
            return interaction_form(user, org, values, details, status=400)
        interactions.create(conn(), user, org_id, values, date.today())
        return redirect(f"/organizacijas/{org_id}?mijiedarbiba=1#mijiedarbibas", code=303)

    # --- F4 · pieprasījumi --------------------------------------------------------

    def request_form(user, org, row=None, values=None, details=(), status=200):
        errors = {d["field"]: org_requests.MESSAGES[(d["field"], d["issue"])] for d in details}
        return render_template("pieprasijums_forma.html", user=user, org=org, row=row, values=values or {},
                               errors=errors, labels=org_requests.FIELD_LABELS, today=date.today()), status

    def editable_request(user, request_id: int):
        row = org_requests.get(conn(), request_id)
        if row is None:
            abort(404)
        if not org_requests.can_edit(user, row):
            abort(403)
        return row

    @app.get("/pieprasijumi")
    def requests_page():
        user = require(*CRM_ROLES)
        status = request.args.get("statuss", "")
        overdue = request.args.get("kaveti") == "1"
        mine = request.args.get("mani") == "1"
        return render_template(
            "pieprasijumi.html", user=user, today=date.today(), status=status, overdue=overdue, mine=mine,
            statuses=org_requests.STATUSES,
            rows=org_requests.list_filtered(conn(), user, date.today(), status, overdue, mine),
        )

    @app.get("/organizacijas/<int:org_id>/pieprasijumi/jauns")
    def request_new(org_id: int):
        user = require(*CRM_ROLES)
        today = date.today()
        values = {"received": today.isoformat(), "due": org_requests.add_month(today).isoformat()}
        return request_form(user, editable_org(user, org_id), values=values)

    @app.post("/organizacijas/<int:org_id>/pieprasijumi/jauns")
    def request_create(org_id: int):
        user = require(*CRM_ROLES)
        org = editable_org(user, org_id)
        values = org_requests.read_form(request.form)
        details = org_requests.validate(values, date.today())
        if details:
            return request_form(user, org, values=values, details=details, status=400)
        request_id = org_requests.create(conn(), user, org_id, values)
        return redirect(f"/pieprasijumi/{request_id}?saglabats=1", code=303)

    @app.get("/pieprasijumi/<int:request_id>")
    def request_card(request_id: int):
        user = require(*CRM_ROLES)
        row = org_requests.get(conn(), request_id)
        if row is None:
            abort(404)
        return render_template(
            "pieprasijums.html", user=user, row=row, today=date.today(), can_edit=org_requests.can_edit(user, row),
            next_status=org_requests.NEXT_STATUS.get(row["status"]), next_action=org_requests.NEXT_ACTION.get(row["status"]),
            overdue=org_requests.is_overdue(row, date.today()), request_tasks=tasks.for_request(conn(), request_id),
            saved="saglabats" in request.args,
        )

    @app.get("/pieprasijumi/<int:request_id>/labot")
    def request_edit(request_id: int):
        user = require(*CRM_ROLES)
        row = editable_request(user, request_id)
        values = dict(row)
        values["description"] = values["description"] or ""
        return request_form(user, organizations.get(conn(), row["organization_id"]), row, values)

    @app.post("/pieprasijumi/<int:request_id>/labot")
    def request_update(request_id: int):
        user = require(*CRM_ROLES)
        row = editable_request(user, request_id)
        values = org_requests.read_form(request.form)
        details = org_requests.validate(values, date.today())
        if details:
            return request_form(user, organizations.get(conn(), row["organization_id"]), row, values, details, 400)
        org_requests.update(conn(), user, request_id, values)
        return redirect(f"/pieprasijumi/{request_id}?saglabats=1", code=303)

    @app.post("/pieprasijumi/<int:request_id>/statuss")
    def request_advance(request_id: int):
        user = require(*CRM_ROLES)
        row = editable_request(user, request_id)
        if not org_requests.advance(conn(), user, row, request.form.get("status", "")):
            abort(400)
        return redirect(f"/pieprasijumi/{request_id}", code=303)

    # --- F5 · uzdevumi -----------------------------------------------------------

    @app.get("/uzdevumi")
    def tasks_page():
        user = require(*CRM_ROLES)
        raw = request.args.get("izpilditajs", "")
        assignee = int(raw) if raw.isdigit() and user["role"] == "vaditajs" else None
        today = date.today()
        return render_template(
            "uzdevumi.html", user=user, today=today, assignee=assignee, staff=users.staff(conn()),
            today_rows=tasks.due_today(conn(), user, today, assignee),
            upcoming_rows=tasks.upcoming(conn(), user, today, assignee),
            done_rows=tasks.recently_done(conn(), user, assignee), created="izveidots" in request.args,
        )

    def task_form(user, values, details=(), status=200):
        errors = {d["field"]: tasks.MESSAGES[(d["field"], d["issue"])] for d in details}
        if "link" in errors and not values.get("request_id"):
            errors["organization_id"] = errors.pop("link")  # kļūdu kopsavilkuma saite ved uz izvēles lauku
        org = organizations.get(conn(), values["organization_id"]) if values.get("organization_id") else None
        req = org_requests.get(conn(), values["request_id"]) if values.get("request_id") else None
        return render_template(
            "uzdevums_forma.html", user=user, values=values, errors=errors, labels=tasks.FIELD_LABELS,
            org=org, req=req, today=date.today(),
            staff_options=[(s["id"], s["full_name"] + (" (es)" if s["id"] == user["id"] else "")) for s in users.staff(conn())],
            org_options=[(o["id"], o["name"]) for o in organizations.list_all(conn())],
        ), status

    @app.get("/uzdevumi/jauns")
    def task_new():
        user = require(*CRM_ROLES)
        values = tasks.read_form({
            "organization_id": request.args.get("organizacija", ""),
            "request_id": request.args.get("pieprasijums", ""),
            "assignee_id": str(user["id"]),
            "due": date.today().isoformat(),
        })
        return task_form(user, values)

    @app.post("/uzdevumi/jauns")
    def task_create():
        user = require(*CRM_ROLES)
        values = tasks.read_form(request.form)
        details = tasks.validate(conn(), values, {s["id"] for s in users.staff(conn())})
        if details:
            return task_form(user, values, details, status=400)
        tasks.create(conn(), user, values)
        if values["request_id"]:
            return redirect(f"/pieprasijumi/{values['request_id']}", code=303)
        return redirect("/uzdevumi?izveidots=1", code=303)

    # --- F6 · meklēšana, F7 · pārskats ----------------------------------------------

    @app.get("/meklet")
    def search_page():
        user = require(*CRM_ROLES)
        query = request.args.get("q", "")
        results = search.run(conn(), query)
        return render_template("meklet.html", user=user, query=query, results=results, today=date.today(),
                               min_length=search.MIN_LENGTH)

    @app.get("/parskats")
    def report_page():
        user = require("vaditajs")
        period = report.period_from(request.args.get("periods", ""))
        return render_template("parskats.html", user=user, today=date.today(), **report.build(conn(), date.today(), period))

    # --- F8 · piekļūstamības paziņojums ---------------------------------------------

    @app.get("/pieklustamiba")
    def accessibility_statement():
        """Publiska lapa; rāda pēdējās automātiskās pārbaudes (make a11y) reālos rezultātus."""
        report_path = Path(__file__).resolve().parents[1] / "docs" / "a11y-rezultati.json"
        try:
            a11y = json.loads(report_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            a11y = None
        return render_template("pieklustamiba.html", user=current_user(), a11y=a11y)

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
