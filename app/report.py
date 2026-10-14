"""F7 · pārskats vadītājam: aktivitāte pa darbiniekiem, kavētie pieprasījumi, aktīvākās organizācijas."""

from __future__ import annotations

import math
import sqlite3
from datetime import date, timedelta

PERIODS = (7, 30, 90)
DEFAULT_PERIOD = 30
TOP_N = 5

# Diagrammas ģeometrija (SVG vienībās). Krāsa #0b7fa3 pārbaudīta ar dataviz validatoru.
CHART = {"width": 680, "label_w": 170, "value_w": 40, "row_h": 34, "bar_h": 20, "top": 8, "axis_h": 26}


def period_from(raw: str) -> int:
    return int(raw) if raw.isdigit() and int(raw) in PERIODS else DEFAULT_PERIOD


def activity(conn: sqlite3.Connection, since: date) -> list[sqlite3.Row]:
    """Mijiedarbību skaits periodā pa darbiniekiem (ieraksta autors); arī tie, kam 0."""
    return conn.execute(
        "SELECT u.id, u.full_name, COUNT(i.id) AS n FROM users u "
        "LEFT JOIN interactions i ON i.created_by = u.id AND i.date >= ? "
        "WHERE u.role IN ('darbinieks', 'vaditajs') GROUP BY u.id ORDER BY n DESC, u.full_name",
        (since.isoformat(),),
    ).fetchall()


def top_organizations(conn: sqlite3.Connection, since: date) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT o.id, o.name, COUNT(i.id) AS n FROM organizations o JOIN interactions i ON i.organization_id = o.id "
        "WHERE i.date >= ? GROUP BY o.id ORDER BY n DESC, o.name LIMIT ?",
        (since.isoformat(), TOP_N),
    ).fetchall()


def overdue_requests(conn: sqlite3.Connection, today: date) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT r.id, r.subject, r.status, r.due, o.id AS organization_id, o.name AS organization, "
        "u.full_name AS responsible FROM requests r JOIN organizations o ON o.id = r.organization_id "
        "JOIN users u ON u.id = o.responsible_id WHERE r.status != 'Atbildēts' AND r.due < ? ORDER BY r.due",
        (today.isoformat(),),
    ).fetchall()


def nice_step(max_value: int) -> int:
    """Asu iedaļas solis: 1, 2, 5, 10, 20 … tā, lai būtu 3–6 iedaļas."""
    if max_value <= 5:
        return 1
    raw = max_value / 5
    magnitude = 10 ** math.floor(math.log10(raw))
    return next(m * magnitude for m in (1, 2, 5, 10) if m * magnitude >= raw)


def bar_chart(rows: list[sqlite3.Row]) -> dict:
    """Horizontāla stabiņu diagramma: ģeometrija šablonam (bez JavaScript)."""
    c = CHART
    max_value = max((r["n"] for r in rows), default=0)
    step = nice_step(max_value)
    axis_max = max(step, math.ceil(max_value / step) * step)
    plot_w = c["width"] - c["label_w"] - c["value_w"]
    scale = plot_w / axis_max
    bars = []
    for i, r in enumerate(rows):
        y = c["top"] + i * c["row_h"]
        w = r["n"] * scale
        bars.append({
            "label": r["full_name"], "value": r["n"], "y": y, "bar_y": y + (c["row_h"] - c["bar_h"]) / 2,
            "w": w, "path": _bar_path(c["label_w"], y + (c["row_h"] - c["bar_h"]) / 2, w, c["bar_h"]),
        })
    plot_h = len(rows) * c["row_h"]
    ticks = [{"value": v, "x": c["label_w"] + v * scale} for v in range(0, axis_max + 1, step)]
    return {"bars": bars, "ticks": ticks, "plot_top": c["top"], "plot_bottom": c["top"] + plot_h,
            "height": c["top"] + plot_h + c["axis_h"], **c}


def _bar_path(x: float, y: float, w: float, h: float, r: float = 4) -> str:
    """Stabiņš ar 4px noapaļotu datu galu un taisnu pamatni (dataviz: marks-and-anatomy)."""
    if w <= 0:
        return ""
    r = min(r, w, h / 2)
    return (f"M{x:.1f},{y:.1f} H{x + w - r:.1f} Q{x + w:.1f},{y:.1f} {x + w:.1f},{y + r:.1f} "
            f"V{y + h - r:.1f} Q{x + w:.1f},{y + h:.1f} {x + w - r:.1f},{y + h:.1f} H{x:.1f} Z")


def build(conn: sqlite3.Connection, today: date, period: int) -> dict:
    since = today - timedelta(days=period - 1)
    act = activity(conn, since)
    return {
        "period": period, "periods": PERIODS, "since": since,
        "activity": act, "chart": bar_chart(act), "total": sum(r["n"] for r in act),
        "top": top_organizations(conn, since), "overdue": overdue_requests(conn, today),
    }
