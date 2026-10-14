# CLAUDE.md · «Iesniegumi»

Noteikumi Claude Code, strādājot šajā mapē.

- Prasību avots: `docs/BACKLOG.md` → izstrādātie kritēriji `docs/prasibas.md`. Strādā pie viena US vienlaikus; komita nosaukums sākas ar US-ID.
- Tehnoloģijas: Python 3.12, Flask, Jinja2, SQLite (`schema.sql`, `data.db`). **Bez JS ietvariem**; servera pusē renderēts HTML; JS drīkst tikai uzlabot (lapai jāstrādā arī bez tā).
- Pieejamība: WCAG 2.2 AA (EN 301 549). Katram laukam `<label>`; kļūdas tekstā + `aria-describedby` + kopsavilkums; tabulām `<caption>` un `<th scope>`; statuss tekstā, ne tikai krāsā; `role="status"` paziņojumiem; skip-link; `lang="lv"`.
- Pēc izmaiņām: `make test` un, ja mainīta lapa, `make a11y`. 0 critical/serious.
- MI: `ai.py` funkcijas līgums `ieteikums(apraksts) -> {tema, atbildes_projekts}` nemainās. MI izvadi vienmēr marķē "Ģenerēts ar MI, pārbaudiet pirms lietošanas", nekad nenosūta automātiski, izmantošanu ieraksta `notikumi`.
- **US-15 "Prioritātes vērtējums" NEIMPLEMENTĒT** — tikai riska klasifikācija `docs/mi-riska-novertejums.md`.
- Personas dati: tikai sintētiski; nerakstīt vārdus, e-pastus, aprakstus `logging` žurnālā; "Mans iesniegums" nerāda iesniedzēja datus.
- Manuālo ekrānlasītāja testu un paziņojuma apstiprināšanu veic cilvēks; neatzīmē tos kā izdarītus.
