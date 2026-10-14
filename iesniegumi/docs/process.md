# «Iesniegumi» · izstrādes process

> Kā prasības no [BACKLOG.md](BACKLOG.md) kļūst par strādājošu, pārbaudītu sistēmu. Izpildīts ar Claude Code kā pāri.

## 1. Plūsma

```
BACKLOG.md ──► prasibas.md ──► MI klasifikācija (pirms būvēšanas) ──► US pa vienam ──► testi ──► a11y tests ──► atskaites ──► prezentācija
 (avots)        (kritēriji,      mi-riska-novertejums.md                (komits ar        (pytest)    (axe +        (MI,
                 WCAG, statuss)   US-7, US-10, US-15                     US-ID)                       tastatūra)    pieejamība)
```

1. **Prasības.** No backloga katram US tiek izrakstīti pārbaudāmi pieņemšanas kritēriji ar WCAG 2.2 un MI akta atsaucēm ([prasibas.md](prasibas.md)).
2. **MI klasifikācija pirms koda.** US-7 tiek klasificēts pirms `ai.py` rakstīšanas. US-15 tiek tikai klasificēts un netiek būvēts.
3. **Īstenošana pa US.** Secība: S0 → US-1 → US-2 → US-8 (iedzīvotāja ceļš) → US-3 → US-4 → US-7 (darbinieks) → US-5 (vadītājs) → US-6 → US-9 → US-14.
   Iedzīvotāja ceļš ir pirmais, jo to izmanto manuālajā pieejamības testā.
4. **Katram US:** kods → testi pēc kritērijiem → `make test` → statuss prasībās → komits `US-x: …`.
5. **Pieejamības testēšana:** `make a11y` uz visām lapām (arī formu ar kļūdām) → `a11y-report.md` → labošana → atkārtota palaišana → protokols.
6. **Atskaites un paziņojums** ar reāliem atradumiem.

## 2. Definition of Done (katram US)

- [ ] Visi US pieņemšanas kritēriji [prasibas.md](prasibas.md) izpildīti un atzīmēti ✅
- [ ] Automātiskie testi katram kritērijam (`tests/test_iesn_*.py`), `make test` iziet
- [ ] Lapa strādā **bez JavaScript** (JS tikai uzlabo, piemēram, fokuss uz kļūdu kopsavilkumu)
- [ ] `make a11y`: 0 critical/serious uz skartajām lapām; 320 px bez horizontālas ritināšanas
- [ ] Teksti latviski, vienkāršā valodā; kļūdas saka, kā labot
- [ ] Nav personas datu žurnālā (`logging`); dati sintētiski
- [ ] Komits ar US-ID nosaukumā

## 3. Rīki

| Rīks | Lietojums |
|---|---|
| Python 3.12, Flask, Jinja2, SQLite | Lietotne, servera pusē renderēts HTML |
| pytest | Funkcionālie un pieejamības struktūras testi |
| Playwright + axe-core (`axe-playwright-python`) | `tests/a11y_check.py`: WCAG 2.2 AA, tastatūra, 320 px, 200 % |
| Claude Code + `CLAUDE.md` | Pāru programmēšana; noteikumi, ko Claude ievēro |
| python-pptx | Prezentācija |

## 4. Komandas

```bash
cd iesniegumi
make init     # schema.sql + 10 testa iesniegumi → data.db
make run      # http://localhost:8001
make test     # pytest
make a11y     # axe + tastatūra + reflow → a11y-report.md, a11y-report.json
```

## 5. Lomu sadalījums cilvēks ↔ Claude

| Darbs | Kas |
|---|---|
| Prasību izrakstīšana, kods, testi, automātiskie pieejamības testi | Claude (cilvēks pārskata) |
| MI riska klasifikācijas melnraksts | Claude; **juridisko secinājumu apstiprina cilvēks / jurists** |
| Manuālais tests ar ekrānlasītāju (NVDA) | **Tikai cilvēks** |
| Paziņojuma apstiprināšana (atbildīgā persona) | **Tikai cilvēks** |
