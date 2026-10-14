"""Ekrāni 2–8. Katra US maršruti tiek pievienoti savā sadaļā."""

from __future__ import annotations

from flask import Flask


def register_views(app: Flask) -> None:
    """Pagaidu vietturi, lai navigācija strādā jau S0 posmā; aizstāj attiecīgie US."""

    @app.get("/iesniegt")
    def iesniegt():
        return "US-1", 200

    @app.get("/darbinieks/iesniegumi")
    def saraksts():
        return "US-3", 200

    @app.get("/vaditajs/parskats")
    def parskats():
        return "US-5", 200
