"""F9 · vadības panelis pēc pieslēgšanās. Servera pusē renderēts HTML, strādā bez JavaScript."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import date, timedelta
from html import escape

ROLE_LABELS = {
    "darbinieks": "Darbinieks",
    "vaditajs": "Vadītājs",
    "administrators": "Administrators",
}
WEEKDAYS = ["pirmdiena", "otrdiena", "trešdiena", "ceturtdiena", "piektdiena", "sestdiena", "svētdiena"]
MONTHS = [
    "janvāris", "februāris", "marts", "aprīlis", "maijs", "jūnijs",
    "jūlijs", "augusts", "septembris", "oktobris", "novembris", "decembris",
]
UPCOMING_DAYS = 7
LIST_LIMIT = 5


# --- Dati ----------------------------------------------------------------------


@dataclass
class Scope:
    """Darbinieks redz savas organizācijas, vadītājs visu iestādi (N3)."""

    user_id: int
    whole_institution: bool

    def org_filter(self, column: str = "o.responsible_id") -> tuple[str, tuple]:
        if self.whole_institution:
            return "1 = 1", ()
        return f"{column} = ?", (self.user_id,)


def stats(conn: sqlite3.Connection, scope: Scope, today: date) -> dict[str, int]:
    where, params = scope.org_filter()
    t = today.isoformat()
    task_where = "1 = 1" if scope.whole_institution else "t.assignee_id = ?"
    task_params = () if scope.whole_institution else (scope.user_id,)
    return {
        "organizations": conn.execute(
            f"SELECT COUNT(*) FROM organizations o WHERE {where}", params
        ).fetchone()[0],
        "open_requests": conn.execute(
            f"SELECT COUNT(*) FROM requests r JOIN organizations o ON o.id = r.organization_id "
            f"WHERE r.status != 'Atbildēts' AND {where}",
            params,
        ).fetchone()[0],
        "contacts_to_review": conn.execute(
            f"SELECT COUNT(*) FROM contacts c JOIN organizations o ON o.id = c.organization_id "
            f"WHERE c.retain_until < ? AND {where}",
            (t, *params),
        ).fetchone()[0],
        "tasks_today": conn.execute(
            f"SELECT COUNT(*) FROM tasks t WHERE t.done_at IS NULL AND t.due <= ? AND {task_where}",
            (t, *task_params),
        ).fetchone()[0],
    }


def tasks_today(conn: sqlite3.Connection, scope: Scope, today: date) -> list[sqlite3.Row]:
    task_where = "1 = 1" if scope.whole_institution else "t.assignee_id = ?"
    task_params = () if scope.whole_institution else (scope.user_id,)
    return conn.execute(
        f"SELECT t.id, t.description, t.due, t.assignee_id, u.full_name AS assignee, o.name AS organization "
        f"FROM tasks t JOIN users u ON u.id = t.assignee_id "
        f"LEFT JOIN organizations o ON o.id = t.organization_id "
        f"WHERE t.done_at IS NULL AND t.due <= ? AND {task_where} "
        f"ORDER BY t.due, t.id LIMIT ?",
        (today.isoformat(), *task_params, LIST_LIMIT),
    ).fetchall()


def urgent_requests(conn: sqlite3.Connection, scope: Scope, today: date) -> list[sqlite3.Row]:
    where, params = scope.org_filter()
    horizon = (today + timedelta(days=UPCOMING_DAYS)).isoformat()
    return conn.execute(
        f"SELECT r.id, r.subject, r.due, r.status, o.name AS organization "
        f"FROM requests r JOIN organizations o ON o.id = r.organization_id "
        f"WHERE r.status != 'Atbildēts' AND r.due <= ? AND {where} "
        f"ORDER BY r.due, r.id",
        (horizon, *params),
    ).fetchall()


def recent_interactions(conn: sqlite3.Connection, scope: Scope) -> list[sqlite3.Row]:
    where, params = scope.org_filter()
    return conn.execute(
        f"SELECT i.date, i.kind, i.summary, o.name AS organization "
        f"FROM interactions i JOIN organizations o ON o.id = i.organization_id "
        f"WHERE {where} ORDER BY i.date DESC, i.id DESC LIMIT ?",
        (*params, LIST_LIMIT),
    ).fetchall()


def pending_users(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT full_name, email, created_at FROM users WHERE role IS NULL ORDER BY created_at"
    ).fetchall()


def complete_task(conn: sqlite3.Connection, task_id: int, user: sqlite3.Row, now: str) -> bool:
    """Atzīmē uzdevumu kā izpildītu. Darbinieks var tikai savus, vadītājs jebkuru."""
    row = conn.execute("SELECT assignee_id FROM tasks WHERE id = ? AND done_at IS NULL", (task_id,)).fetchone()
    if row is None:
        return False
    if user["role"] != "vaditajs" and row["assignee_id"] != user["id"]:
        return False
    conn.execute("UPDATE tasks SET done_at = ? WHERE id = ?", (now, task_id))
    conn.commit()
    return True


# --- Formatēšana ---------------------------------------------------------------


def fmt_date(value: str) -> str:
    d = date.fromisoformat(value[:10])
    return f"{d.day:02d}.{d.month:02d}.{d.year}"


def long_date(d: date) -> str:
    return f"{WEEKDAYS[d.weekday()].capitalize()}, {d.year}. gada {d.day}. {MONTHS[d.month - 1]}"


def due_label(due: str, today: date) -> tuple[str, str]:
    """Termiņa teksts un CSS klase. Statuss vienmēr ir izteikts ar tekstu, ne tikai krāsu (N1)."""
    days = (date.fromisoformat(due) - today).days
    if days < 0:
        return f"KAVĒTS ({-days} d.)", "late"
    if days == 0:
        return "Termiņš šodien", "soon"
    return f"Termiņš pēc {days} d.", "upcoming"


def first_sentence(text: str) -> str:
    head, sep, _ = text.partition(". ")
    return head + ("." if sep else "")


def plural(n: int, one: str, many: str) -> str:
    # Latviešu valodā vienskaitlis, ja skaitlis beidzas ar 1, bet ne ar 11
    return one if n % 10 == 1 and n % 100 != 11 else many


# --- HTML ----------------------------------------------------------------------


def page(title: str, body: str, user: sqlite3.Row | None = None) -> str:
    header_user = ""
    if user is not None:
        role = ROLE_LABELS.get(user["role"] or "", "Gaida apstiprinājumu")
        header_user = f"""
        <div class="topbar-user">
          <span class="topbar-name">{escape(user["full_name"])}<small>{escape(role)}</small></span>
          <form method="post" action="/iziet">
            <button type="submit" class="btn-ghost">Iziet</button>
          </form>
        </div>"""
    return f"""<!doctype html>
<html lang="lv">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)} · Ezermalas pieteikumu sistēma</title>
  <link rel="stylesheet" href="/static/style.css">
</head>
<body class="app">
  <a class="skip-link" href="#saturs">Pāriet uz saturu</a>
  <header class="topbar">
    <a class="topbar-brand" href="/panelis">
      <svg class="brand-mark" viewBox="0 0 40 40" aria-hidden="true">
        <circle cx="20" cy="20" r="19" fill="#176a82"/>
        <circle cx="26" cy="15" r="5" fill="#ffd99a"/>
        <path d="M7 24 q4.3-3 8.6 0 t8.6 0 t8.6 0" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round"/>
        <path d="M10 29.5 q3.3-2.4 6.6 0 t6.6 0 t6.6 0" fill="none" stroke="#fff" stroke-opacity="0.7" stroke-width="2" stroke-linecap="round"/>
      </svg>
      <span>Ezermalas novada pašvaldība<small>Pieteikumu sistēma</small></span>
    </a>
    <nav aria-label="Galvenā navigācija">
      <a href="/panelis" aria-current="page">Sākums</a>
    </nav>{header_user}
  </header>
  <main id="saturs" tabindex="-1">
{body}
  </main>
  <footer class="app-footer">
    © Ezermalas novada pašvaldība · mācību prototips ·
    Foto: Usmas ezers, <a href="https://commons.wikimedia.org/wiki/File:Usmas_ezers,_2015.jpg">WikedKentaur</a>,
    <a href="https://creativecommons.org/licenses/by-sa/4.0/deed.lv">CC BY-SA 4.0</a>
  </footer>
</body>
</html>
"""


def hero(user: sqlite3.Row, today: date, subtitle: str) -> str:
    first_name = user["full_name"].split(" ")[0]
    return f"""    <section class="hero" aria-labelledby="sveiciens">
      <div class="hero-inner">
        <p class="hero-date">{escape(long_date(today))}</p>
        <h1 id="sveiciens">Labdien, {escape(first_name)}!</h1>
        <p class="hero-sub">{escape(subtitle)}</p>
      </div>
    </section>"""


def stat_cards(s: dict[str, int], whole_institution: bool) -> str:
    n = s["organizations"]
    org_label = (
        plural(n, "organizācija iestādē", "organizācijas iestādē")
        if whole_institution
        else plural(n, "mana organizācija", "manas organizācijas")
    )
    cards = [
        (n, org_label, ""),
        (s["open_requests"], plural(s["open_requests"], "atvērts pieprasījums", "atvērti pieprasījumi"), ""),
        (s["tasks_today"], plural(s["tasks_today"], "uzdevums šodien", "uzdevumi šodien"), "warn" if s["tasks_today"] else ""),
        (s["contacts_to_review"], plural(s["contacts_to_review"], "kontakts jāpārskata", "kontakti jāpārskata"), "warn" if s["contacts_to_review"] else ""),
    ]
    items = "\n".join(
        f'        <li class="stat {cls}"><span class="stat-value">{value}</span> <span class="stat-label">{escape(label)}</span></li>'
        for value, label, cls in cards
    )
    return f"""    <section aria-labelledby="kopsavilkums">
      <h2 id="kopsavilkums" class="visually-hidden">Kopsavilkums</h2>
      <ul class="stats">
{items}
      </ul>
    </section>"""


def tasks_block(rows: list[sqlite3.Row], today: date, show_assignee: bool) -> str:
    if not rows:
        content = '<p class="empty">Šodien uzdevumu nav.</p>'
    else:
        items = []
        for r in rows:
            label, cls = due_label(r["due"], today)
            label = "Nokavēts" if cls == "late" else "Šodien"
            meta = [escape(r["organization"])] if r["organization"] else []
            if show_assignee:
                meta.append(escape(r["assignee"]))
            items.append(f"""          <li class="task">
            <div>
              <span class="tag {cls}">{label}</span>
              <span class="task-title">{escape(r["description"])}</span>
              <span class="meta">{" · ".join(meta)}</span>
            </div>
            <form method="post" action="/uzdevumi/{r["id"]}/izpildits">
              <button type="submit" class="btn-small">Izpildīts<span class="visually-hidden">: {escape(r["description"])}</span></button>
            </form>
          </li>""")
        content = '<ul class="task-list">\n' + "\n".join(items) + "\n        </ul>"
    return f"""      <section class="block" aria-labelledby="uzdevumi">
        <h2 id="uzdevumi">Uzdevumi šodien</h2>
        {content}
      </section>"""


def requests_block(rows: list[sqlite3.Row], today: date) -> str:
    if not rows:
        content = '<p class="empty">Kavētu vai tuvojošos pieprasījumu nav.</p>'
    else:
        body_rows = []
        for r in rows:
            label, cls = due_label(r["due"], today)
            body_rows.append(f"""            <tr>
              <th scope="row">{escape(r["subject"])}</th>
              <td>{escape(r["organization"])}</td>
              <td>{escape(r["status"])}</td>
              <td><span class="tag {cls}">{escape(label)}</span> <span class="meta">{fmt_date(r["due"])}</span></td>
            </tr>""")
        content = f"""<div class="table-wrap">
          <table>
            <caption class="visually-hidden">Kavētie pieprasījumi un pieprasījumi ar termiņu nākamajās {UPCOMING_DAYS} dienās</caption>
            <thead>
              <tr><th scope="col">Temats</th><th scope="col">Organizācija</th><th scope="col">Statuss</th><th scope="col">Termiņš</th></tr>
            </thead>
            <tbody>
{chr(10).join(body_rows)}
            </tbody>
          </table>
        </div>"""
    return f"""      <section class="block" aria-labelledby="pieprasijumi">
        <h2 id="pieprasijumi">Kavētie un tuvojošies pieprasījumi</h2>
        {content}
      </section>"""


def interactions_block(rows: list[sqlite3.Row]) -> str:
    if not rows:
        content = '<p class="empty">Mijiedarbību vēl nav.</p>'
    else:
        items = "\n".join(
            f"""          <li>
            <span class="meta">{fmt_date(r["date"])} · {escape(r["kind"])}</span>
            <span class="feed-org">{escape(r["organization"])}</span>
            <span>{escape(first_sentence(r["summary"]))}</span>
          </li>"""
            for r in rows
        )
        content = f'<ul class="feed">\n{items}\n        </ul>'
    return f"""      <section class="block block-wide" aria-labelledby="mijiedarbibas">
        <h2 id="mijiedarbibas">Pēdējās mijiedarbības</h2>
        {content}
      </section>"""


def render_dashboard(conn: sqlite3.Connection, user: sqlite3.Row, today: date) -> str:
    role = user["role"]
    if role is None:
        return page("Konts gaida apstiprinājumu", f"""    <section class="notice-page">
      <h1>Konts gaida apstiprinājumu</h1>
      <p>Paldies, {escape(user["full_name"])}! Jūsu konts ir izveidots, bet administrators vēl nav piešķīris tam lomu.
      Kad loma būs piešķirta, šeit redzēsiet savu vadības paneli.</p>
    </section>""", user)

    if role == "administrators":
        rows = pending_users(conn)
        if rows:
            items = "\n".join(
                f"            <tr><th scope=\"row\">{escape(r['full_name'])}</th><td>{escape(r['email'])}</td><td>{fmt_date(r['created_at'])}</td></tr>"
                for r in rows
            )
            pending = f"""<div class="table-wrap">
          <table>
            <caption class="visually-hidden">Lietotāji, kas gaida lomas piešķiršanu</caption>
            <thead><tr><th scope="col">Vārds</th><th scope="col">E-pasts</th><th scope="col">Reģistrējies</th></tr></thead>
            <tbody>
{items}
            </tbody>
          </table>
        </div>"""
        else:
            pending = '<p class="empty">Neviens lietotājs negaida apstiprinājumu.</p>'
        body = f"""{hero(user, today, "Sistēmas pārvaldība")}
    <ul class="stats">
      <li class="stat {'warn' if rows else ''}"><span class="stat-value">{len(rows)}</span> <span class="stat-label">{plural(len(rows), "lietotājs gaida lomu", "lietotāji gaida lomu")}</span></li>
    </ul>
    <div class="blocks">
      <section class="block block-wide" aria-labelledby="gaida">
        <h2 id="gaida">Lietotāji, kas gaida lomu</h2>
        {pending}
      </section>
    </div>"""
        return page("Vadības panelis", body, user)

    whole = role == "vaditajs"
    scope = Scope(user_id=user["id"], whole_institution=whole)
    subtitle = "Pārskats par visu iestādi" if whole else "Jūsu organizācijas, uzdevumi un termiņi"
    body = f"""{hero(user, today, subtitle)}
{stat_cards(stats(conn, scope, today), whole)}
    <div class="blocks">
{tasks_block(tasks_today(conn, scope, today), today, show_assignee=whole)}
{requests_block(urgent_requests(conn, scope, today), today)}
{interactions_block(recent_interactions(conn, scope))}
    </div>"""
    return page("Vadības panelis", body, user)
