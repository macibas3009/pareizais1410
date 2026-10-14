# Pieejamības atskaite · «Iesniegumi»

> 2026-10-14 · Pēc veidnes [PIEEJAMIBAS-PRASIBAS.md](PIEEJAMIBAS-PRASIBAS.md) 3.–4. sadaļas. Mērķis: **WCAG 2.2 AA** (EN 301 549 V4.1.1; MK 445 prasa 2.1 AA).
> Sagatavoja: Claude Code (automātiskās un automatizējamās pārbaudes) · **Ekrānlasītāja tests un apstiprināšana: cilvēks** (nav veikts).
> Saistīts: [../a11y-report.md](../a11y-report.md) (axe rezultāts), `a11y-protokols.json`, lapa `/pieklustamiba`.

## 1. Kopsavilkums

| | Rezultāts |
|---|---|
| Automātiskais tests (axe-core 4.12.1, WCAG 2.0/2.1/2.2 A+AA) | **0 pārkāpumu** 14 lapās un stāvokļos (arī forma ar kļūdām, lapa pēc statusa maiņas, MI projekts laukā) |
| Tastatūras ceļš (sākums → loma → iesniegt ar kļūdu → apstiprinājums → mans iesniegums) | **6/6 soļi OK** (automatizēts ar Playwright, tikai tastatūra) |
| Reflow 320 px un 200 % mērogs | **0** lapu ar horizontālu ritināšanu |
| Redzams fokuss (Tab cauri katrai lapai) | **0** problēmu |
| Protokola pārbaudes (nosaukumi, virsraksti, orientieri, lauku nosaukumi, mērķu izmērs, paziņojumi) | Atrastas **4 problēmas**, visas **izlabotas** (sk. 5. nodaļu) |
| Ekrānlasītājs (NVDA) | ⬜ **Nav veikts** — jāveic cilvēkam uz Windows |
| **Secinājums** | **Daļēji atbilst.** Automātiski pārbaudāmajā daļā atbilst WCAG 2.2 AA; pilnu atbilstību nevar apliecināt bez ekrānlasītāja testa |

**Svarīgākā mācība:** axe pirmajā palaišanā neatrada nevienu problēmu, bet protokola pārbaudes atrada 4. Automātiskie rīki pārbauda tikai daļu prasību — tas atbilst veidnes brīdinājumam ("tipiski 30–50 %").

## 2. Kontrolsaraksts (veidnes 3. sadaļa)

| # | Prasība | WCAG | Kā pārbaudīts | Rezultāts |
|---|---|---|---|---|
| 1 | Diagrammai teksta alternatīva | 1.1.1 | axe; `<svg role="img">` ar `<title>`/`<desc>`; tie paši dati tabulā (`test_chart_has_text_alternative…`) | ✅ |
| 2 | Virsrakstu hierarhija, tabulu galvenes, lauku saistība | 1.3.1 | axe `heading-order`, `th-has-data-cells`, `label`; `a11y_protokols.py`: viens h1, bez izlaistiem līmeņiem | ✅ |
| 3 | Krāsa nav vienīgais nesējs | 1.4.1 | Statuss tekstā ("Jauns", ne tikai punkts); obligātums tekstā "(obligāts)"; testi | ✅ (pelēktoņu filtrs nav lietots — pēc konstrukcijas) |
| 4 | Kontrasts ≥ 4,5:1 / UI ≥ 3:1 | 1.4.3, 1.4.11 | axe `color-contrast`; diagrammas krāsa `#0b7fa3` pārbaudīta ≥ 3:1; foto: aprēķins (atradums #4) | ✅ / 🟡 foto jāapstiprina ar pipeti |
| 5 | 200 % un 320 px bez zuduma | 1.4.4, 1.4.10 | `a11y_check.py`: 320 px un 640 CSS px visās lapās | ✅ |
| 6 | Viss ar tastatūru, nav lamatu | 2.1.1, 2.1.2 | Tastatūras ceļš 6/6; Tab līdz kājenei | ✅ |
| 7 | Skip-link, nosaukums, secība, saišu teksts | 2.4.1–2.4.4 | Pirmais Tab = "Pāriet uz saturu"; nosaukumi unikāli (pēc labojuma #3); "Iesniegums 2026-0001" | ✅ |
| 8 | Fokuss redzams un nav aizsegts | 2.4.7, 2.4.11 | Tab cauri visām lapām; galvene nav fiksēta (tests `test_no_fixed_header`) | ✅ |
| 9 | Mērķa izmērs ≥ 24×24 | 2.5.8 | `a11y_protokols.py` mēra visas pogas, laukus, navigāciju | ✅ (pēc labojuma #1) |
| 10 | Lapas valoda | 3.1.1 | `<html lang="lv">`, axe `html-has-lang` | ✅ |
| 11 | Konsekventa navigācija; palīdzība vienā vietā | 3.2.3, 3.2.4, 3.2.6 | Viens `base.html`: izvēlne un kontakti kājenē visās lapās | ✅ |
| 12 | Kļūdas identificētas, marķētas, ieteikts labojums | 3.3.1–3.3.3 | Tukša forma: kopsavilkums + ziņa pie lauka (`aria-describedby`) + fokuss uz kopsavilkumu; ziņas saka kā labot | ✅ |
| 13 | Nav atkārtotas ievades; nav kognitīvu testu | 3.3.7, 3.3.8 | Saite "Pārbaudīt iesnieguma … statusu" ar numuru; nav CAPTCHA; kļūdas gadījumā vērtības saglabājas | ✅ |
| 14 | Statusa ziņas nolasa bez fokusa maiņas | 4.1.3 | `role="status"`; pēc pārlādes arī lapas nosaukumā (atradums #2) | 🟡 jāpārbauda ar NVDA |
| 15 | Vilkšanai alternatīva | 2.5.7 | Vilkšanas nav | ✅ (nav piemērojams) |

## 3. Testēšanas protokols (veidnes 4. sadaļa)

### A. Automātiski — `make a11y`

| Lapa / stāvoklis | axe | Nepilnīgi | 320 px | 200 % | Fokuss |
|---|---|---|---|---|---|
| 1 Sākumlapa | 0 | 1 (kontrasts uz foto, #4) | OK | OK | OK |
| 2 Iesnieguma forma | 0 | 0 | OK | OK | OK |
| 2 Forma ar kļūdām | 0 | 0 | OK | OK | OK |
| 3 Apstiprinājums | 0 | 0 | OK | OK | OK |
| 4 Saraksts / ar filtriem | 0 / 0 | 0 | OK | OK | OK |
| 5 Detaļas / pēc statusa maiņas / MI projekts laukā | 0 / 0 / 0 | 0 | OK | OK | OK |
| 6 Pārskats | 0 | 1 (diagrammas skaitļi "par īsu tekstam" — kļūdains signāls: tumšs teksts uz balta) | OK | OK | OK |
| 7 Paziņojums | 0 | 0 | OK | OK | OK |
| 8 Mans iesniegums / rezultāts / nav atrasts | 0 / 0 / 0 | 0 | OK | OK | OK |

Lighthouse un WAVE šajā vidē netika palaisti (nav grafiskā pārlūka paplašinājumu); axe ir tas pats dzinējs, ko izmanto Lighthouse pieejamības sadaļa.

### B. Tastatūra (automatizēts ar Playwright, tikai `Tab`/`Enter`/`Space`/bultiņas)

| Pārbaude | Rezultāts | Piezīme |
|---|---|---|
| Pirmais Tab atver «Pāriet uz saturu» | ☑ OK | |
| Fokuss redzams uz katra elementa | ☑ OK | 3 px kontūra; pārbaudīts katrā lapā |
| Secība loģiska (pa lapu no augšas uz leju) | ☑ OK | DOM secība = vizuālā secība (nav `tabindex > 0`, nav CSS pārkārtošanas); **vizuāli jāapstiprina cilvēkam** |
| Formu var iesniegt ar Enter; radio ar bultiņām | ☑ OK | Iesniegšana ar Enter; tēmas izvēle ar bultiņu; radio pogu sistēmā nav (lomas — pogas) |
| Pēc kļūdas fokuss nonāk uz kļūdu kopsavilkumu | ☑ OK | `#kludas` (JS uzlabojums; bez JS kopsavilkums ir lapas sākumā ar `role="alert"`) |
| Nav vietas, kur fokuss «iestrēgst» | ☑ OK | Tab sasniedz kājeni |

### C. Mērogs un reflow

320 px un 640 CSS px (= 200 % no 1280 px) visās 14 lapās: nav horizontālas ritināšanas. Tabulas šaurā ekrānā ritinās
savā laukumā (`.table-wrap`), kas ir atļauts 1.4.10 izņēmums datu tabulām. Ekrānuzņēmums: [ekrani/8-forma-320px.png](ekrani/8-forma-320px.png).

### D. Ekrānlasītājs

**Ar NVDA nav pārbaudīts** (Codespace vidē nav Windows un ekrānlasītāja). Tālāk — tas, ko var pārbaudīt automātiski
no pieejamības koka (`tests/a11y_protokols.py`). Tas **neaizstāj** NVDA testu.

| Pārbaude | Ko redz pieejamības koks | NVDA |
|---|---|---|
| Lapas nosaukums tiek nolasīts, atverot lapu | Visi nosaukumi unikāli un aprakstoši, piem. «Iesniegums reģistrēts: 2026-0011», «Kļūda: Iesniegt iesniegumu» | ⬜ |
| H taustiņš: virsraksti loģiskā secībā | Katrā lapā viens h1, bez izlaistiem līmeņiem | ⬜ |
| D taustiņš: banner, navigation, main, contentinfo | Visās lapās ir `header`, `nav`, viens `main`, `footer` | ⬜ |
| Laukiem nosaukums, obligātums, kļūda | Visiem laukiem `<label>`, `required`; kļūdas `aria-describedby` + `aria-invalid` | ⬜ |
| Tabulā kolonnu galvenes | `<th scope="col">`, rindu galvenes `<th scope="row">`, `<caption>` | ⬜ |
| Pēc statusa maiņas paziņojums nolasīts | Paziņojums `role="status"`, lapas nosaukumā un fokusā pēc pārlādes | ⬜ |
| MI bloks nosaukts kā «Ģenerēts ar MI …» | `<section aria-labelledby="mi-virsraksts">` + teksts «Ģenerēts ar MI, pārbaudiet pirms lietošanas» | ⬜ |

### E. Saturs (pašnovērtējums)

- Kļūdu ziņas saka, **kā** labot: «Ievadiet e-pastu formā vards@domens.lv», «Izvēlieties tēmu… Ja neviena neder, izvēlieties «Cits»».
- Saišu teksts saprotams ārpus konteksta: «Iesniegums 2026-0001», «Pārbaudīt iesnieguma 2026-0011 statusu».
- Pogas saka darbību un sekas: «Nosūtīt atbildi: mainīt statusu uz «Atbildēts»».
- **Jāvērtē cilvēkam:** vai teksti ir pietiekami vienkārši (piem., senioriem); apstiprinājuma lapas "Kas notiks tālāk".

## 4. Kas jādara cilvēkam

1. NVDA tests (10 min, Windows + NVDA + Firefox/Chrome) pa ceļu "iesniegt iesniegumu" — aizpildīt D tabulu.
2. Kontrasts uz sākumlapas fotogrāfijas — pārbaudīt ar DevTools krāsu pipeti (atradums #4).
3. Vizuāli apstiprināt fokusa secību un 200 % mērogu reālā pārlūkā (Ctrl +).
4. Paziņojumā ierakstīt apstiprinātāju (vārds, amats) — lapa `/pieklustamiba`.

## 5. Atradumu reģistrs

| # | Lapa | Problēma | WCAG | Smagums | Labots (commit) / Paliek paziņojumā |
|---|---|---|---|---|---|
| 1 | Iesnieguma forma; galvene | Piekrišanas rūtiņa 20×20 px; saite «Izvēlēties lomu» 22 px augsta | 2.5.8 | Vidējs | Labots `0a94862` → 24×24 px |
| 2 | Detaļas pēc statusa maiņas | Pēc POST→redirect paziņojums `role="status"` jau ir lapā ielādes brīdī — ekrānlasītāji to parasti nenolasa; fokuss uz `body`; nosaukums nemainās | 4.1.3, 2.4.2 | Augsts (darbinieks nezina, vai darbība izdevās) | Labots `0a94862`: paziņojums lapas nosaukumā + fokuss uz paziņojumu. **Jāapstiprina ar NVDA** |
| 3 | Saraksts; detaļas | Neaprakstoši/dublēti nosaukumi: «Iesniegumi · Iesniegumi · …»; detaļām pirms un pēc darbības vienāds | 2.4.2 | Zems | Labots `0a94862` |
| 4 | Sākumlapa | Teksts uz fotogrāfijas: axe nevar izmērīt kontrastu; aprēķinātais sliktākais gadījums labajā pusē < 4,5:1 | 1.4.3 | Vidējs | Labots `62e7aa8`: pārklājums ≥ 0,62 teksta zonā (sliktākais 4,82:1), telefonā vienmērīgs. Paliek paziņojumā līdz manuālai pārbaudei |
| 5 | Visas lapas | Ekrānlasītāja tests nav veikts | 1.3.1, 4.1.2, 4.1.3 | — | **Paliek paziņojumā** |

Atkārtota pārbaude pēc labojumiem: `make a11y` — 0 pārkāpumu; `a11y_protokols.py` — 0 problēmu.
