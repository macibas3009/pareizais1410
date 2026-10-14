"""Ezermalas pieteikumu sistēma · lietotāju reģistrācija un pieslēgšanās (CR-4).

Palaišana: `make run` (uvicorn --factory app.main:create_app),
tad atver http://localhost:8000/login
"""

from __future__ import annotations

import logging
import os
import re
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from starlette.exceptions import HTTPException as StarletteHTTPException

from app import db, security

VERSION = "0.1.0"
STATIC = Path(__file__).parent / "static"
SESSION_COOKIE = "session"
SESSION_TTL = timedelta(hours=8)
PASSWORD_MIN, PASSWORD_MAX = 12, 128

# Visi latviešu burti; vārdus var atdalīt ar atstarpi, defisi vai apostrofu
FULL_NAME_RE = re.compile(r"^[^\W\d_]+(?:[ '\-][^\W\d_]+)*$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

log = logging.getLogger("app")


class RegisterIn(BaseModel):
    email: str
    fullName: str
    password: str


class LoginIn(BaseModel):
    email: str
    password: str


def error(status: int, code: str, message: str, details: list[dict] | None = None) -> JSONResponse:
    body: dict[str, Any] = {"code": code, "message": message}
    if details:
        body["details"] = details
    return JSONResponse({"error": body}, status_code=status)


def validation_error(details: list[dict]) -> JSONResponse:
    return error(400, "VALIDATION_ERROR", "Request validation failed", details)


def user_out(row) -> dict:
    return {"id": row["id"], "email": row["email"], "fullName": row["full_name"]}


def create_app(db_path: Path | None = None, cookie_secure: bool | None = None) -> FastAPI:
    db_path = db_path or Path(os.environ.get("APP_DB_PATH", "data/app.db"))
    if cookie_secure is None:
        cookie_secure = os.environ.get("COOKIE_SECURE", "0") == "1"

    conn = db.connect(db_path)
    lock = threading.Lock()

    app = FastAPI(title="Ezermalas pieteikumu sistēma", version=VERSION)
    app.mount("/static", StaticFiles(directory=STATIC), name="static")

    # --- Kļūdas vienotā Error shēmā -------------------------------------------

    @app.exception_handler(RequestValidationError)
    async def on_validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        details = []
        for err in exc.errors():
            loc = [str(part) for part in err["loc"] if part != "body"]
            issue = "REQUIRED" if err["type"] == "missing" else "INVALID_FORMAT"
            details.append({"field": ".".join(loc) or "body", "issue": issue})
        return validation_error(details)

    @app.exception_handler(StarletteHTTPException)
    async def on_http_error(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        if exc.status_code == 404:
            return error(404, "NOT_FOUND", "Resource not found")
        return error(exc.status_code, "HTTP_ERROR", str(exc.detail))

    @app.exception_handler(Exception)
    async def on_unexpected(_: Request, exc: Exception) -> JSONResponse:
        # Tikai kļūdas tips, nekad pieprasījuma saturs (CR-4 #10)
        log.error("Unhandled error: %s", type(exc).__name__)
        return error(500, "INTERNAL_ERROR", "Internal server error")

    # --- Sesiju palīgfunkcijas ------------------------------------------------

    def current_user(request: Request):
        token = request.cookies.get(SESSION_COOKIE)
        if not token:
            return None
        now = datetime.now(timezone.utc).isoformat()
        with lock:
            return conn.execute(
                "SELECT u.* FROM sessions s JOIN users u ON u.id = s.user_id "
                "WHERE s.token_hash = ? AND s.expires_at > ?",
                (security.token_hash(token), now),
            ).fetchone()

    # --- Lapas ----------------------------------------------------------------

    @app.get("/", include_in_schema=False)
    def index() -> RedirectResponse:
        return RedirectResponse("/login")

    @app.get("/login", include_in_schema=False)
    def login_page() -> FileResponse:
        return FileResponse(STATIC / "login.html")

    @app.get("/register", include_in_schema=False)
    def register_page() -> FileResponse:
        return FileResponse(STATIC / "register.html")

    @app.get("/profile", include_in_schema=False)
    def profile_page() -> FileResponse:
        return FileResponse(STATIC / "profile.html")

    # --- API ------------------------------------------------------------------

    @app.get("/health", tags=["Sistēma"])
    def health() -> dict:
        return {"status": "ok", "version": VERSION}

    @app.post("/auth/register", tags=["Autentifikācija"], status_code=201)
    def register(payload: RegisterIn):
        email = payload.email.strip().lower()
        full_name = payload.fullName.strip()
        password = payload.password

        details = []
        if not email:
            details.append({"field": "email", "issue": "REQUIRED"})
        elif not EMAIL_RE.fullmatch(email) or len(email) > 254:
            details.append({"field": "email", "issue": "INVALID_FORMAT"})
        if not full_name:
            details.append({"field": "fullName", "issue": "REQUIRED"})
        elif not FULL_NAME_RE.fullmatch(full_name) or len(full_name) > 100:
            details.append({"field": "fullName", "issue": "INVALID_FORMAT"})
        if not password:
            details.append({"field": "password", "issue": "REQUIRED"})
        elif len(password) < PASSWORD_MIN:
            details.append({"field": "password", "issue": "TOO_SHORT"})
        elif len(password) > PASSWORD_MAX:
            details.append({"field": "password", "issue": "TOO_LONG"})
        if details:
            return validation_error(details)

        password_hash = security.hash_password(password)
        with lock:
            if conn.execute("SELECT 1 FROM users WHERE email = ?", (email,)).fetchone():
                return error(409, "EMAIL_TAKEN", "Email is already registered")
            cur = conn.execute(
                "INSERT INTO users (email, full_name, password_hash, created_at) VALUES (?, ?, ?, ?)",
                (email, full_name, password_hash, datetime.now(timezone.utc).isoformat()),
            )
            conn.commit()
        log.info("User registered: id=%s", cur.lastrowid)
        return {"id": cur.lastrowid, "email": email, "fullName": full_name}

    @app.post("/auth/login", tags=["Autentifikācija"])
    def login(payload: LoginIn, response: Response):
        email = payload.email.strip().lower()
        with lock:
            row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        stored = row["password_hash"] if row else security.DUMMY_HASH
        if not security.verify_password(payload.password, stored) or row is None:
            log.warning("Failed login attempt")
            return error(401, "INVALID_CREDENTIALS", "Invalid email or password")

        token = security.new_session_token()
        expires = datetime.now(timezone.utc) + SESSION_TTL
        with lock:
            conn.execute(
                "INSERT INTO sessions (token_hash, user_id, expires_at) VALUES (?, ?, ?)",
                (security.token_hash(token), row["id"], expires.isoformat()),
            )
            conn.commit()
        response.set_cookie(
            SESSION_COOKIE,
            token,
            max_age=int(SESSION_TTL.total_seconds()),
            httponly=True,
            samesite="lax",
            secure=cookie_secure,
        )
        return user_out(row)

    @app.post("/auth/logout", tags=["Autentifikācija"], status_code=204)
    def logout(request: Request) -> Response:
        token = request.cookies.get(SESSION_COOKIE)
        if token:
            with lock:
                conn.execute("DELETE FROM sessions WHERE token_hash = ?", (security.token_hash(token),))
                conn.commit()
        response = Response(status_code=204)
        response.delete_cookie(SESSION_COOKIE)
        return response

    @app.get("/auth/me", tags=["Autentifikācija"])
    def me(request: Request):
        user = current_user(request)
        if user is None:
            return error(401, "UNAUTHENTICATED", "Not logged in")
        return user_out(user)

    return app

