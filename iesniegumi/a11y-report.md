# Pieejamības automātiskā testa atskaite (`tests/a11y_check.py`)

Pārbaudīts: 2026-10-14T10:05+00:00 · axe-core 4.12.1 · WCAG 2.0/2.1/2.2 A un AA · Chromium (Playwright)

## Kopsavilkums

| Rādītājs | Vērtība |
|---|---|
| Pārbaudītas lapas / stāvokļi | 14 (izlaistas, vēl nav: 0) |
| Critical/serious pārkāpumi | **0** |
| Moderate/minor pārkāpumi | 0 |
| Lapas ar horizontālu ritināšanu (320 px / 200 %) | 0 |
| Lapas ar neredzamu fokusu | 0 |
| Tastatūras ceļa soļi, kas neizdevās | 0 |

## Lapas

| Lapa | axe pārkāpumi | Nepilnīgi (jāvērtē manuāli) | 320 px | 200 % | Fokuss |
|---|---|---|---|---|---|
| 1 Sākumlapa: lomas izvēle | 0 | 1 | OK | OK | OK |
| 2 Iesnieguma forma | 0 | 0 | OK | OK | OK |
| 7 Piekļūstamības paziņojums | 0 | 0 | OK | OK | OK |
| 8 Mans iesniegums | 0 | 0 | OK | OK | OK |
| 8 Mans iesniegums: rezultāts | 0 | 0 | OK | OK | OK |
| 8 Mans iesniegums: nav atrasts | 0 | 0 | OK | OK | OK |
| 2 Iesnieguma forma ar kļūdām | 0 | 0 | OK | OK | OK |
| 3 Apstiprinājums | 0 | 0 | OK | OK | OK |
| 4 Saraksts | 0 | 0 | OK | OK | OK |
| 4 Saraksts ar filtriem | 0 | 0 | OK | OK | OK |
| 5 Detaļas | 0 | 0 | OK | OK | OK |
| 5 Detaļas pēc statusa maiņas | 0 | 0 | OK | OK | OK |
| 5 Detaļas: MI projekts atbildes laukā | 0 | 0 | OK | OK | OK |
| 6 Pārskats vadītājam | 0 | 1 | OK | OK | OK |

## Tastatūras ceļš (iedzīvotājs)

| Pārbaude | Rezultāts | Piezīme |
|---|---|---|
| Pirmais Tab atver «Pāriet uz saturu» | OK | Pāriet uz saturu |
| Loma izvēlēta ar Enter | OK | http://127.0.0.1:45837/iesniegt |
| Pēc kļūdas fokuss nonāk uz kļūdu kopsavilkumu | OK | fokuss: #kludas |
| Formu var aizpildīt un iesniegt ar tastatūru | OK | http://127.0.0.1:45837/iesniegts/2026-0012 |
| No apstiprinājuma uz «Mans iesniegums» ar numuru | OK | http://127.0.0.1:45837/mans-iesniegums?numurs=2026-0012 |
| Nav vietas, kur fokuss «iestrēgst» (var aiziet līdz kājenei) | OK |  |

Automātiskie rīki atrod tikai daļu problēmu. Ekrānlasītāja pārbaude (NVDA) jāveic cilvēkam — sk. docs/pieejamibas-atskaite.md.
