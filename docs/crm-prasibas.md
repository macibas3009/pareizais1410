# CRM mazai iestādei · prasību specifikācija

> Versija 1.0 · 2026-10-14 · Statuss: precizēts pēc intervijas ar produkta īpašnieku.
> Avots: uzdevums-starteris "CRM mazai iestādei" un konceptuālās arhitektūras shēma.
> Mācību projekts. Visi dati ir sintētiski.

## 1. Situācija un mērķis

Iestāde ar ~25 darbiniekiem sadarbojas ar uzņēmumiem, NVO un pašvaldībām:
konsultācijas, semināri, pieprasījumi. Šobrīd informācija ir Excel tabulās un
personīgajos e-pastos, un neviens nezina, kas ar ko pēdējo reizi runāja.

**Mērķis:** viena klientu attiecību sistēma (CRM), kurā ir redzamas organizācijas,
kontaktpersonas, mijiedarbības, pieprasījumi un uzdevumi.

## 2. Tehnoloģijas un ierobežojumi (N4)

| Joma | Lēmums |
|---|---|
| Lietotne | Flask, viens process, viena repozitorija |
| Saskarne | Jinja2 šabloni, servera pusē renderēts HTML; `base.html` ar skip-link, orientieriem un fokusa stiliem |
| JavaScript | Nav obligāts: visas funkcijas strādā bez JS. JS drīkst tikai uzlabot |
| Dati | SQLite (`data.db`) |
| Formas | POST → redirect → GET |
| MI | `ai.py`: Claude API vai atslēgvārdu imitācija ar vienādu funkcijas līgumu |
| Vide | GitHub Codespace + Claude Code; `git commit` katrai prasībai |
| Laiks | 1,5 h. Apjoms: **viss F1–F8 + MI-1** (sk. 9. nodaļu par prioritātēm) |
| Sākumdati | 10 organizācijas, 20 kontaktpersonas, 30 mijiedarbības, sintētiski |
| Valoda | Saskarne latviski |

## 3. Lomas un piekļuve (N3)

Pieslēgšanās: **lomas izvēle sākumlapā bez parolēm**. Sākumlapā izvēlas lietotāju
no saraksta. Katrā lapā ir skaidri redzama atzīme "Mācību režīms: bez autentifikācijas".
Izvēlētais lietotājs un loma glabājas sesijā.

| Darbība | Darbinieks | Vadītājs | Administrators |
|---|:-:|:-:|:-:|
| Skatīt un meklēt visas organizācijas un kontaktus | ✔ | ✔ | — |
| Izveidot organizāciju (kļūst par atbildīgo) | ✔ | ✔ | — |
| Labot organizāciju un tās kontaktus | tikai savas¹ | visas | — |
| Pievienot mijiedarbību jebkurai organizācijai | ✔ | ✔ | — |
| Pievienot un mainīt pieprasījumus | tikai savām¹ | visām | — |
| Izveidot uzdevumu sev vai kolēģim | ✔ | ✔ | — |
| Redzēt uzdevumus | savus | visus | — |
| Pārskats (F7) | — | ✔ | — |
| Pārvaldīt lietotājus un lomas | — | — | ✔ |
| Skatīt piekļuves žurnālu | — | — | ✔ |
| Izpildīt kontaktpersonas dzēšanu pēc pieprasījuma | — | — | ✔ |
| Pārskatīt kontaktus ar beigušos glabāšanas termiņu | savējos¹ | visus | ✔ |

¹ "Savas" = organizācijas, kurās lietotājs ir norādīts kā atbildīgais darbinieks.

Administrators ikdienā CRM datus neapstrādā: viņa ekrāni ir lietotāji, piekļuves
žurnāls un dzēšanas pieprasījumi.

## 4. Funkcionālās prasības

### F1 · Organizācijas: izveidot, rediģēt, meklēt

| Lauks | Obligāts | Noteikumi |
|---|:-:|---|
| Nosaukums | ✔ | 2–200 rakstzīmes |
| Reģistrācijas nr. | ✔ | Unikāls. Formāts: sk. 10. nodaļu (atvērts) |
| Veids | ✔ | `Uzņēmums` / `NVO` / `Pašvaldība` |
| Atbildīgais darbinieks | ✔ | Lietotājs ar lomu Darbinieks vai Vadītājs |

**Pieņemšanas kritēriji**
1. Saraksts ir tabula ar `<caption>` un `<th scope="col">`; to var filtrēt pēc veida un atbildīgā.
2. Formā katram laukam ir `<label>`. Kļūdu gadījumā lapas augšā ir kļūdu kopsavilkums ar saitēm uz laukiem, un pie katra lauka ir kļūdas teksts (`aria-describedby`). Ievadītās vērtības tiek saglabātas.
3. Ja reģistrācijas nr. dublējas, parādās kļūda "Organizācija ar šo reģ. nr. jau ir reģistrēta".
4. Organizācijas kartītē ir pamatdati, kontaktpersonas, mijiedarbību hronoloģija (jaunākā augšā), pieprasījumi un uzdevumi.
5. Katra kartītes atvēršana tiek ierakstīta piekļuves žurnālā (N2).
6. Darbinieks, kurš nav atbildīgais, kartītē neredz pogu "Labot". Tieša pieeja labošanas URL atgriež 403.

### F2 · Kontaktpersonas pie organizācijas

| Lauks | Obligāts | Noteikumi |
|---|:-:|---|
| Vārds, uzvārds | ✔ | Latviešu burti, atstarpe, defise |
| Amats | ✔ | |
| E-pasts | vismaz viens no abiem | Derīgs formāts |
| Tālrunis | vismaz viens no abiem | Formāts: sk. 10. nodaļu (atvērts) |
| Saziņas pamats | ✔ | Vienīgā vērtība: `Līgums` |
| Saziņas pamata datums | ✔ | Līguma vai sadarbības sākuma datums |
| Glabāt līdz | automātiski | Pēdējās mijiedarbības datums + 3 gadi (ja nav mijiedarbību, tad izveides datums + 3 gadi) |

**Pieņemšanas kritēriji**
1. Formā ir tikai šie lauki, citu personas datu lauku nav (datu minimizācija). Nav lauka "piezīmes par personu".
2. "Glabāt līdz" netiek ievadīts. Tas tiek pārrēķināts pēc katras mijiedarbības, kurā kontakts piedalās.
3. Kontaktu kartītes atvēršana tiek ierakstīta piekļuves žurnālā.

### F3 · Mijiedarbību žurnāls

| Lauks | Obligāts | Noteikumi |
|---|:-:|---|
| Veids | ✔ | `Zvans` / `E-pasts` / `Sanāksme` |
| Datums | ✔ | Nevar būt nākotnē |
| Dalībnieki | ✔ | Viena vai vairākas organizācijas kontaktpersonas + darbinieki |
| Kopsavilkums | ✔ | Līdz 2000 rakstzīmēm |
| Nākamais solis | — | Līdz 500 rakstzīmēm |

**Pieņemšanas kritēriji**
1. Mijiedarbības ir redzamas organizācijas kartītē hronoloģiski, jaunākā augšā.
2. Jebkurš darbinieks var pievienot mijiedarbību jebkurai organizācijai.
3. Kopsavilkumu var izveidot ar MI-1. Šādam kopsavilkumam ir atzīme "Ģenerēts ar MI, apstiprināja <darbinieks>".
4. Pēc saglabāšanas tiek pārrēķināts dalībnieku "Glabāt līdz" (F2).

### F4 · Pieprasījumi no organizācijām

| Lauks | Obligāts | Noteikumi |
|---|:-:|---|
| Organizācija | ✔ | |
| Temats | ✔ | Līdz 200 rakstzīmēm |
| Apraksts | — | Līdz 2000 rakstzīmēm |
| Saņemts | ✔ | Noklusēti šodiena |
| Termiņš | ✔ | Noklusēti saņemšanas datums + 1 mēnesis; var mainīt |
| Statuss | ✔ | `Jauns` → `Darbā` → `Atbildēts` |

**Pieņemšanas kritēriji**
1. Statuss mainās tikai uz priekšu: Jauns → Darbā → Atbildēts.
2. **Kavēts** = termiņš ir pagājis un statuss nav `Atbildēts`. To aprēķina, nevis glabā.
3. Kavētie pieprasījumi ir izcelti ar **tekstu** "KAVĒTS (N d.)" un ikonu ar tekstuālu alternatīvu, ne tikai ar krāsu.
4. Sarakstu var filtrēt pēc statusa un pēc tā, vai pieprasījums ir kavēts.

### F5 · Uzdevumi un atgādinājumi

| Lauks | Obligāts | Noteikumi |
|---|:-:|---|
| Apraksts | ✔ | Līdz 300 rakstzīmēm |
| Izpildītājs | ✔ | Pats vai kolēģis |
| Izpildes datums | ✔ | |
| Saistīts ar | ✔ | Organizācija **vai** pieprasījums |
| Izpildīts | — | Atzīme + izpildes laiks |

**Pieņemšanas kritēriji**
1. Lapā "Mani uzdevumi šodien" ir izpildītāja uzdevumi ar datumu ≤ šodiena, kas nav izpildīti. Nokavētie ir augšā ar teksta atzīmi "Nokavēts".
2. Atzīmēt "Izpildīts" var ar vienu pogu (POST formu), bez JS.
3. Vadītājs redz visu darbinieku uzdevumus.
4. Atgādinājumi ir tikai sistēmā (sākumlapā un sarakstā). E-pasta paziņojumi ir ārpus apjoma.

### F6 · Meklēšana

**Pieņemšanas kritēriji**
1. Viens meklēšanas lauks galvenē, pieejams visās lapās (`role="search"`, ar `<label>`).
2. Meklē organizāciju nosaukumos un reģ. nr., kontaktpersonu vārdos un e-pastos, pieprasījumu tematos.
3. Mijiedarbību teksts netiek meklēts (VDAR minimizācija).
4. Vismaz 2 rakstzīmes. Meklēšana nav jutīga pret lielajiem un mazajiem burtiem, un garumzīmes ir jāievada.
5. Rezultāti ir tabulā ar `<caption>` ("Meklēšanas rezultāti: N atrasti") un `<th scope>`, sagrupēti pēc veida.
6. Darbinieks redz visus rezultātus (sk. 3. nodaļu). Kontaktpersonas kartītes atvēršana no rezultātiem tiek ierakstīta žurnālā.

### F7 · Pārskats vadītājam

**Pieņemšanas kritēriji**
1. Periodu var izvēlēties: 7 / 30 / 90 dienas, noklusēti 30.
2. Pārskatā ir:
   - aktivitāte pa darbiniekiem: mijiedarbību skaits periodā;
   - kavētie pieprasījumi: saraksts un skaits;
   - aktīvākās organizācijas: top 5 pēc mijiedarbību skaita periodā.
3. Katrai diagrammai blakus ir **tā pati informācija tabulā**. Diagrammai ir teksta apraksts (`alt` vai `figcaption`).
4. Pārskats ir pieejams tikai vadītājam. Citām lomām tas atgriež 403.

### F8 · Piekļūstamības paziņojums

**Pieņemšanas kritēriji**
1. Lapa `/pieklustamiba`, saite uz to ir katras lapas kājenē.
2. Saturā ir:
   - atbilstības statuss (EN 301 549 / WCAG 2.2 AA);
   - **reālie testa atradumi** no `tests/a11y_check.py` un manuālajiem testiem;
   - zināmie ierobežojumi;
   - kontakts atsauksmēm;
   - pārbaudes datums.

## 5. MI komponents (`ai.py`)

### MI-1 · Mijiedarbības kopsavilkums un nākamā soļa ieteikums

**Funkcijas līgums:** `kopsavilkums(teksts: str) -> {"kopsavilkums": str, "nakamais_solis": str, "avots": "claude" | "imitacija"}`

| Lēmums | Saturs |
|---|---|
| Darbības režīms | Ja vidē ir `ANTHROPIC_API_KEY`, izmanto Claude API. Citādi izmanto atslēgvārdu imitāciju ar to pašu līgumu |
| Kad teksts tiek nosūtīts ārēji | Tikai pēc tam, kad darbinieks nospiež pogu "Izveidot kopsavilkumu ar MI". Pirms tam ir brīdinājums neiekļaut sensitīvus datus |
| Rezultāts | Ne vairāk kā 3 teikumi + viens ieteikums nākamajam solim |
| Marķējums | Rezultāts ir redzami marķēts "Ģenerēts ar MI" |
| Cilvēka kontrole | Darbinieks rediģē un apstiprina. Bez apstiprinājuma nekas netiek saglabāts |
| Žurnāls | Žurnālā tiek ierakstīts: kurš ģenerēja, kurš apstiprināja, laiks, `avots`. **Nekad** netiek ierakstīts teksts |
| Kļūdas | API kļūdas vai noildzes gadījumā (> 10 s) tiek parādīts paziņojums un piedāvāta imitācija. Lietotājs nekad neredz 500 |
| MI akta klase | Minimāls risks (pārredzamības pienākums: marķējums) |

### MI-2 · Organizāciju prioritizācija "pēc sadarbības potenciāla"

**Lēmums: nebūvēt, tikai klasificēt.** Jāsagatavo klasifikācijas dokuments
`docs/mi2-klasifikacija.md`, kurā ir:
- kas tiktu vērtēts (organizācijas, netieši arī kontaktpersonas);
- kādas sekas tas radītu organizācijai vai personai (piem., mazāk uzmanības, piekļuve pakalpojumiem);
- MI akta riska klases novērtējums (iespējams augsts) un pamatojums;
- lēmums "būvēt vai nē" un nosacījumi, ar kādiem to varētu pārskatīt.

## 6. Nefunkcionālās prasības

### N1 · Piekļūstamība (EN 301 549 / WCAG 2.2 AA)

1. `tests/a11y_check.py` (axe-core + Playwright) uz visiem galvenajiem ekrāniem neatrod **critical** vai **serious** pārkāpumus.
2. Galvenajā ceļā (lomas izvēle → organizācija → mijiedarbība → pieprasījums → uzdevums) visu var izdarīt tikai ar tastatūru, un fokuss vienmēr ir redzams.
3. Lapas ir lietojamas 200 % mērogā un 320 px platumā bez horizontālas ritināšanas.
4. Ir skip-link, orientieri (`header`, `nav`, `main`, `footer`), loģiska virsrakstu secība un unikāli lapu virsraksti.
5. Statusi un kavējumi ir izteikti ar tekstu, ne tikai ar krāsu. Kontrasts ≥ 4.5:1.
6. Manuāls tests ar NVDA galvenajā ceļā. Rezultāti tiek ierakstīti F8 lapā.

### N2 · Personas dati (VDAR)

1. **Minimizācija:** tikai F2 lauki, bez brīva teksta laukiem par personu. Meklēšana nemeklē mijiedarbību tekstā.
2. **Glabāšanas termiņš:** 3 gadi pēc pēdējās mijiedarbības (F2).
3. **Pēc termiņa beigām** kontakts nonāk sarakstā "Jāpārskata". Atbildīgais darbinieks vai vadītājs to pagarina (ar pamatojumu, kas tiek ierakstīts žurnālā) vai dzēš. Automātiskas dzēšanas nav.
4. **Piekļuves žurnāls:** katra organizācijas vai kontaktpersonas kartītes atvēršana tiek ierakstīta (kas, ko, kad, darbība). Žurnālu var skatīt tikai administrators.
5. **Dzēšana pēc pieprasījuma** (veic administrators):
   - kontaktpersonas ieraksts tiek dzēsts neatgriezeniski;
   - mijiedarbībās dalībnieks tiek aizstāts ar "Dzēsta kontaktpersona";
   - žurnālā tiek ierakstīts dzēšanas fakts (kas, kad, ieraksta ID) bez personas datiem.
6. Lietotnes žurnālā (`logging`) netiek rakstīti personas dati un mijiedarbību teksti.

### N3 · Lomas

Skatīt 3. nodaļu.

### N4 · Tehnoloģijas un laiks

Skatīt 2. nodaļu.

## 7. Datu modelis (aptuvens)

| Tabula | Galvenie lauki |
|---|---|
| `lietotaji` | id, vārds, loma (`darbinieks` / `vaditajs` / `administrators`), aktīvs |
| `organizacijas` | id, nosaukums, reg_nr (unikāls), veids, atbildigais_id |
| `kontakti` | id, organizacija_id, vārds, amats, epasts, talrunis, sazinas_pamats, pamata_datums, glabat_lidz |
| `mijiedarbibas` | id, organizacija_id, veids, datums, kopsavilkums, nakamais_solis, mi_generets, apstiprinaja_id, izveidoja_id |
| `mijiedarbibu_dalibnieki` | mijiedarbiba_id, kontakts_id (NULL, ja dzēsts) / lietotajs_id |
| `pieprasijumi` | id, organizacija_id, temats, apraksts, sanemts, termins, statuss |
| `uzdevumi` | id, apraksts, izpilditajs_id, izveidoja_id, datums, organizacija_id / pieprasijums_id, izpildits_laiks |
| `piekluves_zurnals` | id, lietotajs_id, darbiba, objekta_tips, objekta_id, laiks |

## 8. Ekrāni (9)

1. Sākums / lomas izvēle
2. Organizāciju saraksts (+ filtri)
3. Organizācijas kartīte (kontakti, mijiedarbības, pieprasījumi, uzdevumi)
4. Organizācijas forma
5. Kontaktpersonas forma
6. Mijiedarbības forma (+ MI-1)
7. Pieprasījumi un Mani uzdevumi
8. Meklēšanas rezultāti
9. Vadītāja pārskats

Papildus: piekļūstamības paziņojums (F8) un administratora ekrāni (lietotāji, piekļuves žurnāls, dzēšana, "Jāpārskata").

## 9. Prioritātes 1,5 h ietvaros

Apjoms ir viss F1–F8 + MI-1. Ja laiks beidzas, secība ir:

1. Pamats: `base.html` (N1), lomas izvēle (N3), sākumdati
2. F1 → F2 → F3 (ar piekļuves žurnālu, N2)
3. F4 → F5
4. F6 → F7
5. MI-1 (vispirms imitācija, tad Claude API)
6. F8 ar reāliem atradumiem, administratora ekrāni, "Jāpārskata" saraksts

Katrai prasībai atsevišķs komits, kura ziņojums sākas ar prasības ID (piem., `F3: mijiedarbību žurnāls`).

## 10. Atvērtie jautājumi un pieņēmumi

| # | Jautājums | Pieņēmums, līdz tiek atbildēts |
|---|---|---|
| 1 | Reģistrācijas nr. formāts. NVO un pašvaldībām tas ir 11 cipari? | 11 cipari |
| 2 | Tālruņa formāts | `+371` un 8 cipari vai 8 cipari |
| 3 | Vai organizāciju drīkst dzēst? Kurš? | Nedrīkst. Ārpus apjoma |
| 4 | Cik ilgi glabā piekļuves žurnālu? | 1 gads |
| 5 | Saziņas pamats ir tikai "Līgums". Vai kontaktiem bez līguma (piem., semināra dalībniekiem) nav vietas sistēmā? | Jā, šādus kontaktus nereģistrē |
| 6 | Vai pagarinot glabāšanas termiņu vajag pamatojumu no saraksta vai brīvu tekstu? | Brīvs teksts, līdz 200 rakstzīmēm |
| 7 | Kurš Claude modelis MI-1? | Konfigurējams ar vides mainīgo |

## 11. Ārpus apjoma

- Īsta autentifikācija (paroles, SSO). Ražošanas vidē obligāta
- E-pasta paziņojumi un atgādinājumi
- Datu imports no Excel
- Organizāciju dzēšana
- MI-2 īstenošana
- Tulkojumi citās valodās

## 12. Lēmumu žurnāls

| Jautājums | Lēmums | Kas, kad |
|---|---|---|
| Darbinieka piekļuve citu organizācijām | Redz visas, labo savas | Produkta īpašnieks, 2026-10-14 |
| Administratora loma | Tikai pārvaldība (lietotāji, žurnāls, dzēšana) | Produkta īpašnieks, 2026-10-14 |
| Pieslēgšanās | Lomas izvēle bez parolēm (mācību režīms) | Produkta īpašnieks, 2026-10-14 |
| Apjoms 1,5 h | Viss F1–F8 + MI-1 | Produkta īpašnieks, 2026-10-14 |
| Kontakta glabāšanas termiņš | 3 gadi pēc pēdējās mijiedarbības | Produkta īpašnieks, 2026-10-14 |
| Pēc termiņa | Saraksts "Jāpārskata", bez automātiskas dzēšanas | Produkta īpašnieks, 2026-10-14 |
| Dzēšana pēc pieprasījuma | Dzēš kontaktu, mijiedarbības anonimizē | Produkta īpašnieks, 2026-10-14 |
| Saziņas pamats | Tikai "Līgums" | Produkta īpašnieks, 2026-10-14 |
| Pieprasījuma termiņš | 1 mēnesis, var mainīt | Produkta īpašnieks, 2026-10-14 |
| Uzdevumu piešķiršana | Sev un kolēģiem | Produkta īpašnieks, 2026-10-14 |
| MI-1 | Claude API, ja ir atslēga, citādi imitācija | Produkta īpašnieks, 2026-10-14 |
| MI-2 | Tikai klasifikācija, nebūvēt | Produkta īpašnieks, 2026-10-14 |
| Pārskata periods | 7/30/90 d., noklusēti 30; top 5 pēc mijiedarbībām | Produkta īpašnieks, 2026-10-14 |
| Meklēšanas apjoms | Organizācijas, kontakti, pieprasījumi; bez mijiedarbību teksta | Produkta īpašnieks, 2026-10-14 |
