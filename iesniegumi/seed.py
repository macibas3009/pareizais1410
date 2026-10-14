"""S0.2 · 10 sintētiski testa iesniegumi 5 tēmās. Vārdi, adreses un e-pasti ir izdomāti."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone

# (dienas atpakaļ, vārds, tēmas id, vieta, apraksts, statuss, apstrādes dienas, atbilde/pamatojums)
IESNIEGUMI = [
    (1, "Jānis Bērziņš", 1, "Ezera iela 12", "Pie Ezera ielas 12 ir liela bedre, kurā jau iebrauca divas mašīnas. Lūdzu, salabojiet to.", "Jauns", None, None),
    (2, "Līga Ozoliņa", 2, "Parka iela, pie sētas ieejas", "Parka ielā jau nedēļu nedeg trīs ielu lampas, vakaros ir pilnīgi tumšs.", "Jauns", None, None),
    (3, "Pēteris Kalns", 3, "Skolas iela 4", "Atkritumu konteineri pie mājas netiek izvesti jau divas nedēļas, apkārt mētājas maisi.", "Apstrādē", None, None),
    (5, "Dace Liepiņa", 4, "Ezermalas pirmsskola", "Vēlos uzzināt, kura vieta rindā bērnudārzā ir manam dēlam un kad varētu saņemt vietu.", "Apstrādē", None, None),
    (6, "Inese Vītola", 5, "Dzirnavu iela 8-3", "Esmu pensionāre, lūdzu informāciju par mājokļa pabalstu un kādi dokumenti jāiesniedz.", "Jauns", None, None),
    (9, "Raimonds Egle", 1, "Lauku ceļš pie tilta", "Lauku ceļš pēc lietus ir izskalots, grants pazudusi, grūti izbraukt ar autobusu.", "Atbildēts", 4,
     "Paldies par ziņu. Ceļa remonts plānots nākamnedēļ, darbus veiks pašvaldības komunālais dienests."),
    (12, "Santa Krūmiņa", 2, "Stacijas laukums", "Stacijas laukumā lampa mirgo visu nakti, tas traucē kaimiņiem gulēt.", "Atbildēts", 2,
     "Lampa nomainīta 3. datumā. Ja problēma atkārtojas, lūdzu, rakstiet vēlreiz."),
    (15, "Toms Lazdiņš", 3, "Meža iela 20", "Lūdzu uzstādīt dalītās vākšanas konteineru stiklam mūsu ielā.", "Noraidīts", 6,
     "Stikla konteiners jau ir pieejams 200 m attālumā, Meža ielas un Skolas ielas krustojumā. Papildu konteiners nav plānots."),
    (18, "Agnese Priede", 5, "Upes iela 2", "Mana ģimene nonākusi grūtībās pēc darba zaudēšanas, kādu palīdzību varam saņemt?", "Atbildēts", 8,
     "Sociālais darbinieks ar jums sazināsies un vienosies par tikšanos. Līdzi ņemiet ienākumu izziņas."),
    (21, "Valdis Ābele", 4, "Saules pirmsskola", "Vai ir iespējams mainīt bērnudārzu uz tuvāku dzīvesvietai, Saules pirmsskolu?", "Atbildēts", 5,
     "Pieteikums par maiņu reģistrēts. Rindā uz Saules pirmsskolu esat 4. vietā."),
]


def seed(conn: sqlite3.Connection, now: datetime | None = None) -> bool:
    """Ievieto testa iesniegumus, ja tabula ir tukša. Atgriež False, ja dati jau ir."""
    if conn.execute("SELECT 1 FROM iesniegumi LIMIT 1").fetchone():
        return False
    now = now or datetime.now(timezone.utc)
    rows = sorted(IESNIEGUMI, key=lambda r: -r[0])  # vecākie pirmie → mazāki numuri
    for i, (ago, vards, tema, vieta, apraksts, statuss, apstr_dienas, atbilde) in enumerate(rows, start=1):
        created = now - timedelta(days=ago, hours=i)
        numurs = f"{created.year}-{i:04d}"
        epasts = f"iedzivotajs{i}@example.com"
        slegts = (created + timedelta(days=apstr_dienas)).isoformat(timespec="seconds") if apstr_dienas else None
        cur = conn.execute(
            "INSERT INTO iesniegumi (numurs, izveidots, vards, epasts, tema_id, vieta, apraksts, piekrisana, statuss, atbilde, slegts) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?)",
            (numurs, created.isoformat(timespec="seconds"), vards, epasts, tema, vieta, apraksts, statuss, atbilde, slegts),
        )
        iid = cur.lastrowid
        events = [(created, "iedzivotajs", "iesniegts", "Iesniegums reģistrēts")]
        if statuss != "Jauns":
            events.append((created + timedelta(hours=20), "darbinieks", "statuss", "Statuss: Jauns → Apstrādē"))
        if statuss in ("Atbildēts", "Noraidīts"):
            events.append((created + timedelta(days=apstr_dienas), "darbinieks", "statuss", f"Statuss: Apstrādē → {statuss}"))
        conn.executemany(
            "INSERT INTO notikumi (iesniegums_id, laiks, loma, veids, apraksts) VALUES (?, ?, ?, ?, ?)",
            [(iid, t.isoformat(timespec="seconds"), loma, veids, txt) for t, loma, veids, txt in events],
        )
    conn.commit()
    return True
