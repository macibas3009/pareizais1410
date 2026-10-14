# «Iesniegumi» · prasību specifikācija

> Versija 1.0 · 2026-10-14 · Avots: [BACKLOG.md](BACKLOG.md) (kursa backlogs), [PIEEJAMIBAS-PRASIBAS.md](PIEEJAMIBAS-PRASIBAS.md),
> [MI-RISKA-KLASIFIKACIJA.md](MI-RISKA-KLASIFIKACIJA.md). Mācību projekts; Ezermalas novada pašvaldība ir izdomāta, dati sintētiski.

## 1. Mērķis un konteksts

Novada pašvaldība e-pasta kastes vietā vēlas sistēmu iedzīvotāju iesniegumiem: bedres, apgaismojums,
atkritumi, bērnudārza rinda, sociālā palīdzība. Sistēma ir **iestādes tīmekļvietne**, tāpēc uz to attiecas
MK noteikumi Nr. 445 un EN 301 549. Mērķis: **WCAG 2.2 AA**. Sistēmā ir MI komponents (US-7), kas jāklasificē
pēc MI akta pirms būvēšanas.

## 2. Lomas

Lomu izvēlas sākumlapā, bez parolēm (mācību režīms; uz katras lapas redzama atzīme). Loma glabājas sesijā.

| Loma | Ko dara | Ekrāni |
|---|---|---|
| **Iedzīvotājs** | Iesniedz iesniegumu, pārbauda statusu pēc numura | 1, 2, 3, 8, 7 |
| **Darbinieks** | Apstrādā iesniegumus: statuss, komentārs, atbilde, MI ieteikums | 1, 4, 5, 7 |
| **Vadītājs** | Tas pats, ko darbinieks, + pārskats | 1, 4, 5, 6, 7 |

Iedzīvotāja ekrāni (2, 3, 8) un paziņojums (7) ir pieejami bez lomas izvēles. Darbinieka ekrāniem vajag lomu
darbinieks vai vadītājs; pārskatam tikai vadītājs (citādi 403).

## 3. Ekrāni (8)

| # | Ekrāns | Adrese | US |
|---|---|---|---|
| 1 | Sākumlapa: lomas izvēle | `/` | — |
| 2 | Iesnieguma forma ar validāciju | `/iesniegt` | US-1 |
| 3 | Apstiprinājums ar numuru | `/iesniegts/<numurs>` | US-2 |
| 4 | Saraksts ar filtriem | `/darbinieks/iesniegumi` | US-3 |
| 5 | Detaļas: statuss, vēsture, MI ieteikums | `/darbinieks/iesniegumi/<numurs>` | US-4, US-7 |
| 6 | Pārskats vadītājam (tabula + diagramma) | `/vaditajs/parskats` | US-5 |
| 7 | Piekļūstamības paziņojums | `/pieklustamiba` | US-6 |
| 8 | Mans iesniegums: statuss pēc numura | `/mans-iesniegums` | US-8 |

## 4. Datu modelis (`schema.sql`)

| Tabula | Lauki |
|---|---|
| `temas` | id, nosaukums (6 tēmas: Ceļi un bedres, Ielu apgaismojums, Atkritumi, Bērnudārza rinda, Sociālā palīdzība, Cits) |
| `iesniegumi` | id, numurs (`2026-0001`), izveidots, vards, epasts, tema_id, vieta, apraksts, piekrisana, statuss, atbilde, atbildes_projekts, slegts |
| `notikumi` | id, iesniegums_id, laiks, loma, veids, apraksts — katra statusa maiņa, komentārs, atbilde, MI ieteikuma izmantošana |

Statusi: **Jauns → Apstrādē → Atbildēts / Noraidīts**.

## 5. Pieņemšanas kritēriji

Statusa apzīmējumi: ✅ izpildīts un notestēts · 🟡 daļēji · ⬜ nav sākts. Statusu atjauno tajā pašā komitā, kurā prasība tiek īstenota.

### S0 · Iesildīšanās

| # | Kritērijs | Statuss |
|---|---|---|
| S0.1 | `python app.py` startē sistēmu, sākumlapa redzama | ✅ |
| S0.2 | `schema.sql` un 10 testa iesniegumi 5 tēmās `data.db` | ✅ |
| S0.3 | `python tests/a11y_check.py` strādā | ✅ |

### US-1 · Iesnieguma iesniegšana (MUST)

| # | Kritērijs | WCAG | Statuss |
|---|---|---|---|
| 1.1 | Lauki: vārds, e-pasts, tēma (no DB), adrese/vieta, apraksts, piekrišana datu apstrādei | — | ✅ |
| 1.2 | Servera puses validācija: obligātie lauki, e-pasta formāts, tēma no saraksta, apraksts ≤ 3000 rakstzīmes, piekrišana atzīmēta | 3.3.1 | ✅ |
| 1.3 | Pēc kļūdas forma saglabā ievadīto (izņemot neko — nav paroles) | 3.3.7 | ✅ |
| 1.4 | Katram laukam `<label>`; obligātie lauki apzīmēti ar tekstu "(obligāts)", ne tikai krāsu | 1.3.1, 3.3.2, 1.4.1 | ✅ |
| 1.5 | Kļūdas tekstā pie lauka, saistītas ar `aria-describedby`; kļūda saka, kā labot | 3.3.1, 3.3.3 | ✅ |
| 1.6 | Kļūdu kopsavilkums lapas sākumā ar saitēm uz laukiem; fokuss uz kopsavilkumu | 3.3.1 | ✅ |
| 1.7 | Nav laika limita (sesija nebeidzas, kamēr aizpilda) | 2.2.1 | ✅ |

### US-2 · Apstiprinājums (MUST)

| # | Kritērijs | WCAG | Statuss |
|---|---|---|---|
| 2.1 | POST → redirect → apstiprinājuma lapa; F5 nerada dubultu iesniegumu | — | ✅ |
| 2.2 | `<title>` sākas ar "Iesniegums reģistrēts" | 2.4.2 | ✅ |
| 2.3 | Numurs tekstā; paskaidrots, kas notiks tālāk; saite uz "Mans iesniegums" ar jau ievadītu numuru | 1.1.1, 3.3.7 | ✅ |

### US-3 · Iesniegumu saraksts (MUST)

| # | Kritērijs | WCAG | Statuss |
|---|---|---|---|
| 3.1 | Tabula: numurs, datums, tēma, iesniedzējs, statuss; jaunākie augšā | — | ⬜ |
| 3.2 | Filtri pēc statusa un tēmas + meklēšana tekstā (GET forma) | — | ⬜ |
| 3.3 | `<table>` ar `<caption>` (ar skaitu) un `<th scope>` | 1.3.1 | ⬜ |
| 3.4 | Statuss ar tekstu, ne tikai krāsu | 1.4.1 | ⬜ |
| 3.5 | Filtru forma ar `<fieldset><legend>` | 1.3.1 | ⬜ |
| 3.6 | Saites teksts "Iesniegums 2026-0001", ne "Skatīt" | 2.4.4 | ⬜ |

### US-4 · Detaļas un apstrāde (MUST)

| # | Kritērijs | WCAG | Statuss |
|---|---|---|---|
| 4.1 | Statusa maiņa tikai pa atļautajiem soļiem: Jauns → Apstrādē → Atbildēts / Noraidīts | — | ⬜ |
| 4.2 | "Atbildēts" prasa atbildes tekstu; "Noraidīts" prasa pamatojumu | 3.3.1 | ⬜ |
| 4.3 | Komentāra pievienošana; katra maiņa un komentārs ierakstās `notikumi` | — | ⬜ |
| 4.4 | Vēsture hronoloģiski | — | ⬜ |
| 4.5 | Virsrakstu hierarhija h1 → h2 | 1.3.1, 2.4.6 | ⬜ |
| 4.6 | Pēc darbības paziņojums `role="status"` | 4.1.3 | ⬜ |
| 4.7 | Pogas ar skaidru tekstu ("Mainīt statusu uz …") | 4.1.2 | ⬜ |
| 4.8 | Galvene nav fiksēta, fokuss netiek aizsegts | 2.4.11 | ⬜ |

### US-5 · Pārskats vadītājam (MUST)

| # | Kritērijs | WCAG | Statuss |
|---|---|---|---|
| 5.1 | Tabula: skaits pa statusiem; tabula: skaits pa tēmām | 1.3.1 | ⬜ |
| 5.2 | Vidējais apstrādes laiks (dienās no iesniegšanas līdz atbildei/noraidījumam) | — | ⬜ |
| 5.3 | Joslu diagramma (inline SVG); tā pati informācija tabulā | 1.1.1 | ⬜ |
| 5.4 | Joslu kontrasts ≥ 3:1 pret fonu | 1.4.11 | ⬜ |
| 5.5 | Tikai vadītājam (citiem 403) | — | ⬜ |

### US-6 · Piekļūstamības paziņojums (MUST)

| # | Kritērijs | WCAG | Statuss |
|---|---|---|---|
| 6.1 | Lapa `/pieklustamiba` pēc veidnes (MK 445, ES 2018/1523) | — | ⬜ |
| 6.2 | Saite kājenē katrā lapā vienā vietā | 3.2.3, 3.2.6 | ⬜ |
| 6.3 | Saturs aizpildīts ar reāliem testu atradumiem (pēc testēšanas) | — | ⬜ |

### US-7 · MI ieteikums darbiniekam (SHOULD)

| # | Kritērijs | Avots | Statuss |
|---|---|---|---|
| 7.1 | `ai.py`: `ieteikums(apraksts) -> {tema, atbildes_projekts}`; noklusēti atslēgvārdu imitācija bez tīkla; ar `ANTHROPIC_API_KEY` — Claude API ar to pašu līgumu | — | ⬜ |
| 7.2 | Detaļu lapā bloks "MI ieteikums" (`<section aria-labelledby>`) ar marķējumu "Ģenerēts ar MI, pārbaudiet pirms lietošanas" | MI akta 50. p. gars; WCAG 1.3.1 | ⬜ |
| 7.3 | Poga "Izmantot projektu" ieliek tekstu atbildes laukā rediģēšanai; nekad nenosūta automātiski | Cilvēka uzraudzība | ⬜ |
| 7.4 | Izmantošana ierakstās `notikumi` | Žurnāls | ⬜ |
| 7.5 | Bez mirgojoša ielādes indikatora | WCAG 2.3.1 | ⬜ |
| 7.6 | Riska klasifikācija aizpildīta pirms būvēšanas | MI akts | ⬜ |

### US-8 · Mans iesniegums (SHOULD)

| # | Kritērijs | WCAG | Statuss |
|---|---|---|---|
| 8.1 | Forma ar vienu lauku (numurs); rezultāts: statuss, pēdējais notikums, atbilde | — | ✅ |
| 8.2 | Nav CAPTCHA vai puzles | 3.3.8 | ✅ |
| 8.3 | Kļūda "nav atrasts" tekstā, ar formāta paraugu | 3.3.1, 3.3.3 | ✅ |
| 8.4 | Netiek rādīti iesniedzēja personas dati (tikai statuss un atbilde) | VDAR | ✅ |

### US-9 · Pieejamības tests zaļš (SHOULD)

| # | Kritērijs | Statuss |
|---|---|---|
| 9.1 | `tests/a11y_check.py` pārbauda visas lapas, arī formu ar kļūdām → `a11y-report.md` | ⬜ |
| 9.2 | 0 critical/serious | ⬜ |
| 9.3 | Nenovēršamie atradumi dokumentēti paziņojumā | ⬜ |

### US-14 · Reflow 320 px un 200 % (COULD, izvēlēts)

| # | Kritērijs | WCAG | Statuss |
|---|---|---|---|
| 14.1 | 320 px un 640 CSS px (200 %) platumā nav horizontālas ritināšanas, nekas nepazūd | 1.4.4, 1.4.10 | ⬜ |

### Ārpus apjoma

- US-10 čata palīgs, US-11 e-pasta paziņojumi, US-12 CSV, US-13 tumšais režīms: netiek īstenoti. US-10 tiek klasificēts MI novērtējumā.
- **US-15 "Prioritātes vērtējums": NEIMPLEMENTĒT** (backlogā tikai dizainam). Tikai riska klasifikācija.
- Īsta autentifikācija (paroles, eParaksts), e-pasta sūtīšana.

## 6. Atskaites

| Atskaite | Fails | Saturs |
|---|---|---|
| MI riska novērtējums | [mi-riska-novertejums.md](mi-riska-novertejums.md) | Veidne aizpildīta US-7, US-10, US-15 |
| Pieejamības atskaite | [pieejamibas-atskaite.md](pieejamibas-atskaite.md) + `a11y-report.md` | Automātiskais tests, tastatūras protokols, reflow, ekrānlasītāja daļa, atradumu reģistrs |
| Prezentācija | `docs/prezentacija.pptx` | Secība, process, secinājumi |
