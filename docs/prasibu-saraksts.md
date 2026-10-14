# CRM mazai iestādei · prasību saraksts

> Versija 1.8 · 2026-10-14 · Statuss: precizēts pēc intervijas ar produkta īpašnieku.
> Avots: uzdevums-starteris "CRM mazai iestādei" un konceptuālās arhitektūras shēma.
> Mācību projekts. Visi dati ir sintētiski.

## Izpildes statuss

Statusu atjauno tajā pašā komitā, kurā prasība tiek īstenota.
**DONE** tiek atzīmēts tikai tad, kad visi prasības pieņemšanas kritēriji ir izpildīti un notestēti.

| Apzīmējums | Nozīme |
|---|---|
| ✅ DONE | Visi pieņemšanas kritēriji izpildīti un notestēti |
| 🟡 DAĻĒJI | Daļa kritēriju izpildīta (sk. prasības sadaļu) |
| ⬜ NAV SĀKTS | Nav īstenots |

| ID | Prasība | Statuss | Kur īstenots |
|---|---|---|---|
| F0 | Pieslēgšanās un reģistrācija | ✅ DONE | zari `cr-4-auth`, `f9-panelis`, `n4-flask`; lomu apstiprināšana zarā `f0-lomas` |
| F1 | Organizācijas: izveidot, rediģēt, meklēt | ✅ DONE | zars `f0-lomas`; `tests/test_organizations.py` |
| F2 | Kontaktpersonas pie organizācijas | ✅ DONE | zari `crm-2-kontakti`, `crm-3-mijiedarbibas` |
| F3 | Mijiedarbību žurnāls | ✅ DONE | zars `crm-3-mijiedarbibas`; `tests/test_interactions.py` |
| F4 | Pieprasījumi no organizācijām | ✅ DONE | zars `crm-4-pieprasijumi`; `tests/test_requests_tasks.py` |
| F5 | Uzdevumi un atgādinājumi | ✅ DONE | zars `crm-4-pieprasijumi`; `tests/test_requests_tasks.py` |
| F6 | Meklēšana | ✅ DONE | zars `crm-5-meklesana-parskats`; `tests/test_search_report.py` |
| F7 | Pārskats vadītājam | ✅ DONE | zars `crm-5-meklesana-parskats`; `tests/test_search_report.py` |
| F8 | Piekļūstamības paziņojums | ⬜ NAV SĀKTS | |
| F9 | Vadības panelis pēc pieslēgšanās | ✅ DONE | zari `f9-panelis` … `crm-5-meklesana-parskats` |
| MI-1 | Mijiedarbības kopsavilkums un nākamais solis | ✅ DONE | zars `crm-3-mijiedarbibas`; `app/ai.py`; Claude ceļš nav pārbaudīts ar īstu API atslēgu |
| MI-2 | Organizāciju prioritizācija: tikai klasifikācija | ⬜ NAV SĀKTS | |
| N1 | Piekļūstamība | 🟡 DAĻĒJI | 320 px pārbaudīts automātiski visās 21 lapā (`crm-5-meklesana-parskats`); axe un tastatūras testi — 6. posmā |
| N2 | Personas dati (VDAR) | ✅ DONE | zari `crm-2-kontakti` … `crm-5-meklesana-parskats` |
| N3 | Lomas | 🟡 DAĻĒJI | lomu pieprasīšana un apstiprināšana, tiesības F1 un F9; pārējās tiesības nāks ar F2–F7 |
| N4 | Tehnoloģijas un laiks | 🟡 DAĻĒJI | Flask + Jinja2 + SQLite un sākumdati: zars `n4-flask`; 1,5 h nav ievērots |

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
| Laiks | 1,5 h. Apjoms: **viss F0–F9 + MI-1** (sk. 9. nodaļu par prioritātēm) |
| Sākumdati | 10 organizācijas, 20 kontaktpersonas, 30 mijiedarbības, sintētiski |
| Valoda | Saskarne latviski |

## 3. Lomas un piekļuve (N3)

Pieslēgšanās: **ar e-pastu un paroli** (F0). Reģistrējoties lietotājs **pieprasa** lomu (Darbinieks vai Vadītājs); administrators to apstiprina, maina vai noraida. Administratora lomu pieprasīt nevar.
Jauns reģistrēts lietotājs bez lomas redz tikai paziņojumu "Konts gaida apstiprinājumu"
un nekādus CRM datus. Loma tiek nolasīta no datubāzes katrā pieprasījumā, nevis no
sīkdatnes.

> Izmaiņa 2026-10-14: sākotnējais lēmums bija "lomas izvēle bez parolēm (mācību režīms)".
> Aizstāts ar pieslēgšanos ar paroli, jo tā jau ir īstenota (CR-4).

| Darbība | Darbinieks | Vadītājs | Administrators |
|---|:-:|:-:|:-:|
| Vadības panelis (F9) | savi dati | visa iestāde | pārvaldības bloki |
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

### F0 · Pieslēgšanās un reģistrācija

**Statuss: ✅ DONE (7 no 7).** Flask + Jinja2. JSON API no `docs/openapi.yaml` (`/auth/*`) saglabāts.

| Lauks | Obligāts | Noteikumi |
|---|:-:|---|
| Vārds, uzvārds | ✔ | Latviešu burti, atstarpe, defise, apostrofs; līdz 100 rakstzīmēm |
| E-pasts | ✔ | Derīgs formāts, unikāls (nejutīgs pret lielajiem un mazajiem burtiem) |
| Parole | ✔ | Vismaz 12, ne vairāk kā 128 rakstzīmes; jāievada divreiz |

**Pieņemšanas kritēriji**

| # | Kritērijs | Statuss |
|---|---|---|
| 1 | Reģistrācijas forma ar laukiem un kļūdu tekstiem pie katra lauka. Prasība "vismaz 12 rakstzīmes" ir redzama pirms ievades | ✅ DONE |
| 2 | Pieslēgšanās ar e-pastu un paroli. Nepareiza parole un neesošs e-pasts saņem vienādu atbildi "Nepareizs e-pasts vai parole" | ✅ DONE |
| 3 | Parole glabājas tikai kā jaucējvērtība (scrypt). Sesija tiek glabāta HttpOnly sīkdatnē (8 h). Žurnālā nav e-pasta, vārda un paroles | ✅ DONE |
| 4 | Poga "Iziet" beidz sesiju. Vecā sesijas sīkdatne vairs nedarbojas | ✅ DONE |
| 5 | Pēc pieslēgšanās lietotājs nonāk vadības panelī (F9) | ✅ DONE (`f9-panelis`) |
| 6 | Jauns lietotājs bez lomas redz "Konts gaida apstiprinājumu". Lomu piešķir administrators (N3) | ✅ DONE (`f0-lomas`): reģistrācijā pieprasa lomu; administrators panelī apstiprina ar vienu pogu, lapā `/lietotaji` maina lomu, var noraidīt (konts tiek dzēsts); izmaiņas žurnālā; `tests/test_roles_flow.py` |
| 7 | Formas strādā bez JavaScript (N1: POST → redirect → GET). Kļūdu kopsavilkums ar saitēm uz laukiem, ievadītās vērtības saglabājas | ✅ DONE (`n4-flask`, `tests/test_forms.py`) |

Saskarne: ezera fotogrāfija ("Usmas ezers, 2015", WikedKentaur, CC BY-SA 4.0) kreisajā pusē.
Virsraksts atrodas virs horizonta, paskaidrojums zem tā. Autorība ir redzama katrā lapā.

### F1 · Organizācijas: izveidot, rediģēt, meklēt

| Lauks | Obligāts | Noteikumi |
|---|:-:|---|
| Nosaukums | ✔ | 2–200 rakstzīmes |
| Reģistrācijas nr. | ✔ | Unikāls. Formāts: sk. 10. nodaļu (atvērts) |
| Veids | ✔ | `Uzņēmums` / `NVO` / `Pašvaldība` |
| Atbildīgais darbinieks | ✔ | Lietotājs ar lomu Darbinieks vai Vadītājs. Darbiniekam tas ir viņš pats; izvēlēties var tikai vadītājs |

**Statuss: ✅ DONE (6 no 6).** Zars `f0-lomas`. Lapas: `/organizacijas`, `/organizacijas/jauna`, `/organizacijas/<id>`, `/organizacijas/<id>/labot`. Testi: `tests/test_organizations.py`.
Meklēšana pēc nosaukuma būs F6. Kartītē kontakti, pieprasījumi, uzdevumi un mijiedarbības pagaidām ir tikai skatāmi; pievienošana būs F2–F5.

**Pieņemšanas kritēriji**

| # | Kritērijs | Statuss |
|---|---|---|
| 1 | Saraksts ir tabula ar `<caption>` un `<th scope="col">`; to var filtrēt pēc veida un atbildīgā | ✅ DONE |
| 2 | Formā katram laukam ir `<label>`. Kļūdu gadījumā lapas augšā ir kļūdu kopsavilkums ar saitēm uz laukiem, un pie katra lauka ir kļūdas teksts (`aria-describedby`). Ievadītās vērtības tiek saglabātas | ✅ DONE |
| 3 | Ja reģistrācijas nr. dublējas, parādās kļūda "Organizācija ar šo reģ. nr. jau ir reģistrēta" | ✅ DONE |
| 4 | Organizācijas kartītē ir pamatdati, kontaktpersonas, mijiedarbību hronoloģija (jaunākā augšā), pieprasījumi un uzdevumi | ✅ DONE |
| 5 | Katra kartītes atvēršana tiek ierakstīta piekļuves žurnālā (N2) | ✅ DONE |
| 6 | Darbinieks, kurš nav atbildīgais, kartītē neredz pogu "Labot". Tieša pieeja labošanas URL atgriež 403 | ✅ DONE |

### F2 · Kontaktpersonas pie organizācijas

| Lauks | Obligāts | Noteikumi |
|---|:-:|---|
| Vārds, uzvārds | ✔ | Latviešu burti, atstarpe, defise |
| Amats | ✔ | |
| E-pasts | vismaz viens no abiem | Derīgs formāts |
| Tālrunis | vismaz viens no abiem | 8 cipari, var ar `+371` (pieņēmums, 10. nodaļa) |
| Saziņas pamats | ✔ | Vienīgā vērtība: `Līgums` |
| Saziņas pamata datums | ✔ | Līguma vai sadarbības sākuma datums |
| Glabāt līdz | automātiski | Pēdējās mijiedarbības datums + 3 gadi (ja nav mijiedarbību, tad izveides datums + 3 gadi) |

**Statuss: ✅ DONE (3 no 3).** Zari `crm-2-kontakti`, `crm-3-mijiedarbibas`. Lapas: `/organizacijas/<id>/kontakti/jauns`, `/kontakti/<id>`, `/kontakti/<id>/labot`. Testi: `tests/test_contacts.py`.
Kontaktus pievieno un labo organizācijas atbildīgais vai vadītājs. Organizācijas kartītē redzams tikai vārds un amats; e-pasts un tālrunis ir kontaktpersonas kartītē, kuras atvēršana tiek žurnalēta.

**Pieņemšanas kritēriji**

| # | Kritērijs | Statuss |
|---|---|---|
| 1 | Formā ir tikai šie lauki, citu personas datu lauku nav (datu minimizācija). Nav lauka "piezīmes par personu" | ✅ DONE |
| 2 | "Glabāt līdz" netiek ievadīts. Tas tiek pārrēķināts pēc katras mijiedarbības, kurā kontakts piedalās | ✅ DONE: izveidojot = šodiena + 3 gadi; pēc mijiedarbības = pēdējās mijiedarbības datums + 3 gadi |
| 3 | Kontaktu kartītes atvēršana tiek ierakstīta piekļuves žurnālā | ✅ DONE |

### F3 · Mijiedarbību žurnāls

| Lauks | Obligāts | Noteikumi |
|---|:-:|---|
| Veids | ✔ | `Zvans` / `E-pasts` / `Sanāksme` |
| Datums | ✔ | Nevar būt nākotnē |
| Dalībnieki | ✔ | Viena vai vairākas organizācijas kontaktpersonas + darbinieki |
| Kopsavilkums | ✔ | Līdz 2000 rakstzīmēm |
| Nākamais solis | — | Līdz 500 rakstzīmēm |

**Statuss: ✅ DONE (4 no 4).** Zars `crm-3-mijiedarbibas`. Lapa: `/organizacijas/<id>/mijiedarbibas/jauna`. Testi: `tests/test_interactions.py`.
Dalībnieki var būt tikai šīs organizācijas kontaktpersonas un darbinieki. Dzēsta kontaktpersona hronoloģijā redzama kā "Dzēsta kontaktpersona" (N2).

**Pieņemšanas kritēriji**

| # | Kritērijs | Statuss |
|---|---|---|
| 1 | Mijiedarbības ir redzamas organizācijas kartītē hronoloģiski, jaunākā augšā | ✅ DONE |
| 2 | Jebkurš darbinieks var pievienot mijiedarbību jebkurai organizācijai | ✅ DONE |
| 3 | Kopsavilkumu var izveidot ar MI-1. Šādam kopsavilkumam ir atzīme "Ģenerēts ar MI, apstiprināja <darbinieks>" | ✅ DONE |
| 4 | Pēc saglabāšanas tiek pārrēķināts dalībnieku "Glabāt līdz" (F2) | ✅ DONE |

### F4 · Pieprasījumi no organizācijām

| Lauks | Obligāts | Noteikumi |
|---|:-:|---|
| Organizācija | ✔ | |
| Temats | ✔ | Līdz 200 rakstzīmēm |
| Apraksts | — | Līdz 2000 rakstzīmēm |
| Saņemts | ✔ | Noklusēti šodiena |
| Termiņš | ✔ | Noklusēti saņemšanas datums + 1 mēnesis; var mainīt |
| Statuss | ✔ | `Jauns` → `Darbā` → `Atbildēts` |

**Statuss: ✅ DONE (4 no 4).** Zars `crm-4-pieprasijumi`. Lapas: `/pieprasijumi`, `/pieprasijumi/<id>`, `/organizacijas/<id>/pieprasijumi/jauns`, `/pieprasijumi/<id>/labot`. Testi: `tests/test_requests_tasks.py`.

**Pieņemšanas kritēriji**

| # | Kritērijs | Statuss |
|---|---|---|
| 1 | Statuss mainās tikai uz priekšu: Jauns → Darbā → Atbildēts | ✅ DONE |
| 2 | **Kavēts** = termiņš ir pagājis un statuss nav `Atbildēts`. To aprēķina, nevis glabā | ✅ DONE |
| 3 | Kavētie pieprasījumi ir izcelti ar **tekstu** "KAVĒTS (N d.)" un ikonu ar tekstuālu alternatīvu, ne tikai ar krāsu | ✅ DONE |
| 4 | Sarakstu var filtrēt pēc statusa un pēc tā, vai pieprasījums ir kavēts | ✅ DONE |

### F5 · Uzdevumi un atgādinājumi

| Lauks | Obligāts | Noteikumi |
|---|:-:|---|
| Apraksts | ✔ | Līdz 300 rakstzīmēm |
| Izpildītājs | ✔ | Pats vai kolēģis |
| Izpildes datums | ✔ | |
| Saistīts ar | ✔ | Organizācija **vai** pieprasījums |
| Izpildīts | — | Atzīme + izpildes laiks |

**Statuss: ✅ DONE (4 no 4).** Zars `crm-4-pieprasijumi`. Lapas: `/uzdevumi` (vadītājam filtrs pēc izpildītāja), `/uzdevumi/jauns`; poga "Izpildīts" arī panelī un pieprasījuma kartītē. Testi: `tests/test_requests_tasks.py`.

**Pieņemšanas kritēriji**

| # | Kritērijs | Statuss |
|---|---|---|
| 1 | Lapā "Mani uzdevumi šodien" ir izpildītāja uzdevumi ar datumu ≤ šodiena, kas nav izpildīti. Nokavētie ir augšā ar teksta atzīmi "Nokavēts" | ✅ DONE |
| 2 | Atzīmēt "Izpildīts" var ar vienu pogu (POST formu), bez JS | ✅ DONE |
| 3 | Vadītājs redz visu darbinieku uzdevumus | ✅ DONE |
| 4 | Atgādinājumi ir tikai sistēmā (sākumlapā un sarakstā). E-pasta paziņojumi ir ārpus apjoma | ✅ DONE |

### F6 · Meklēšana

**Statuss: ✅ DONE (6 no 6).** Zars `crm-5-meklesana-parskats`. Lapa `/meklet`, lauks galvenē darbiniekam un vadītājam. Testi: `tests/test_search_report.py`.

**Pieņemšanas kritēriji**

| # | Kritērijs | Statuss |
|---|---|---|
| 1 | Viens meklēšanas lauks galvenē, pieejams visās lapās (`role="search"`, ar `<label>`) | ✅ DONE |
| 2 | Meklē organizāciju nosaukumos un reģ. nr., kontaktpersonu vārdos un e-pastos, pieprasījumu tematos | ✅ DONE |
| 3 | Mijiedarbību teksts netiek meklēts (VDAR minimizācija) | ✅ DONE |
| 4 | Vismaz 2 rakstzīmes. Meklēšana nav jutīga pret lielajiem un mazajiem burtiem, un garumzīmes ir jāievada | ✅ DONE |
| 5 | Rezultāti ir tabulā ar `<caption>` ("Meklēšanas rezultāti: N atrasti") un `<th scope>`, sagrupēti pēc veida | ✅ DONE |
| 6 | Darbinieks redz visus rezultātus (sk. 3. nodaļu). Kontaktpersonas kartītes atvēršana no rezultātiem tiek ierakstīta žurnālā | ✅ DONE |

### F7 · Pārskats vadītājam

**Statuss: ✅ DONE (4 no 4).** Zars `crm-5-meklesana-parskats`. Lapa `/parskats`. Diagramma: servera pusē zīmēts SVG (bez JS), krāsa `#0b7fa3` pārbaudīta ar validatoru, `<title>` uznirstošais teksts katram stabiņam. Testi: `tests/test_search_report.py`.

**Pieņemšanas kritēriji**

| # | Kritērijs | Statuss |
|---|---|---|
| 1 | Periodu var izvēlēties: 7 / 30 / 90 dienas, noklusēti 30 | ✅ DONE |
| 2 | Pārskatā ir: aktivitāte pa darbiniekiem: mijiedarbību skaits periodā; kavētie pieprasījumi: saraksts un skaits; aktīvākās organizācijas: top 5 pēc mijiedarbību skaita periodā | ✅ DONE |
| 3 | Katrai diagrammai blakus ir **tā pati informācija tabulā**. Diagrammai ir teksta apraksts (`alt` vai `figcaption`) | ✅ DONE |
| 4 | Pārskats ir pieejams tikai vadītājam. Citām lomām tas atgriež 403 | ✅ DONE |

### F8 · Piekļūstamības paziņojums

**Pieņemšanas kritēriji**
1. Lapa `/pieklustamiba`, saite uz to ir katras lapas kājenē.
2. Saturā ir:
   - atbilstības statuss (EN 301 549 / WCAG 2.2 AA);
   - **reālie testa atradumi** no `tests/a11y_check.py` un manuālajiem testiem;
   - zināmie ierobežojumi;
   - kontakts atsauksmēm;
   - pārbaudes datums.

### F9 · Vadības panelis pēc pieslēgšanās

Kopsavilkuma skats, kas tiek atvērts uzreiz pēc pieslēgšanās (F0) un kad lietotājs
noklikšķina uz zīmola vai saites "Sākums". Saturs ir atkarīgs no lomas.

**Bloki darbiniekam**

| Bloks | Saturs | Avots |
|---|---|---|
| Kopsavilkuma skaitļi | Manas organizācijas · mani atvērtie pieprasījumi · mani kontakti "Jāpārskata" · mani uzdevumi šodien | F1, F4, N2, F5 |
| Mani uzdevumi šodien | Skaits + pirmie 5; nokavētie augšā ar teksta atzīmi "Nokavēts"; poga "Izpildīts" | F5 |
| Kavētie un tuvojošies pieprasījumi | Manu organizāciju kavētie pieprasījumi un tie, kam termiņš ir nākamajās 7 dienās; teksts "KAVĒTS (N d.)" vai "Termiņš pēc N d." | F4 |
| Pēdējās mijiedarbības | 5 jaunākās manu organizāciju mijiedarbības: datums, organizācija, veids, kopsavilkuma pirmais teikums | F3 |

**Vadītājam** ir tie paši bloki par **visu iestādi**, nevis tikai par savām organizācijām, kā arī saite "Atvērt pilno pārskatu" uz F7.
**Administratoram** panelī ir: lietotāji, kas gaida lomas piešķiršanu, atvērtie dzēšanas pieprasījumi un saite uz piekļuves žurnālu.

**Statuss: ✅ DONE (7 no 7).** Sākts zarā `f9-panelis`, pabeigts zarā `crm-5-meklesana-parskats`. Testi: `tests/test_dashboard.py`, `tests/test_requests_tasks.py`.
Trūkstošās daļas ir atkarīgas no sarakstiem un pārskata, kas vēl nav uztaisīti (F3, F4, F5, F7).

**Pieņemšanas kritēriji**

| # | Kritērijs | Statuss |
|---|---|---|
| 1 | Pēc veiksmīgas pieslēgšanās lietotājs tiek novirzīts uz `/panelis`. Bez sesijas `/panelis` novirza uz `/login` | ✅ DONE |
| 2 | Katram blokam ir virsraksts (`h2`). Saraksti ir tabulas ar `<caption>` vai saraksti (`ul`). Katrā blokā ir saite "Skatīt visus" uz pilno sarakstu | ✅ DONE: "Skatīt visus uzdevumus", "Skatīt visus pieprasījumus", "Skatīt visas organizācijas" |
| 3 | Skaitļi ir teksts ar paskaidrojumu (piem., "3 kavēti pieprasījumi"), nevis tikai krāsa vai ikona. Katrs skaitlis ir saite uz atfiltrētu sarakstu | ✅ DONE: visas kartes ir saites uz atfiltrētiem sarakstiem |
| 4 | Ja blokā nav datu, tiek parādīts teksts, piem., "Šodien uzdevumu nav" | ✅ DONE |
| 5 | Darbinieks redz tikai savu organizāciju datus. Vadītājs redz visas iestādes datus (N3) | ✅ DONE: vadītājam arī saite "Atvērt pilno pārskatu" (F7); administratoram lomu apstiprināšana, dzēšanas pieprasījumi un žurnāls |
| 6 | Paneļa atvēršana netiek ierakstīta piekļuves žurnālā. Žurnālā tiek ierakstīta kartītes atvēršana no paneļa saitēm (N2) | ✅ DONE |
| 7 | Panelis atbilst N1: 320 px platumā bloki izkārtojas vienā kolonnā, un tas strādā bez JavaScript | ✅ DONE: bez JS notestēts; 320 px pārbaudīts ar Playwright (nav horizontālas ritināšanas) |

**Papildus īstenots:** uzdevumu var atzīmēt kā izpildītu tieši no paneļa (POST forma). Darbinieks to var tikai saviem uzdevumiem, vadītājs jebkuram.
Testa lietotāji (sākumdati, `make seed`): `darbinieks@example.com`, `darbinieks2@example.com`, `vaditajs@example.com`, `admin@example.com`. Parole ir `app/seed.py` vai vides mainīgajā `SEED_PASSWORD`.

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

**Statuss: ✅ DONE.** `app/ai.py`, forma `/organizacijas/<id>/mijiedarbibas/jauna`. Testi: `tests/test_interactions.py`.

| Lēmums | Kā īstenots |
|---|---|
| Darbības režīms | ✅ Claude API (`claude-opus-5-5`, maināms ar `MI_MODEL`, strukturēta JSON atbilde), ja ir `ANTHROPIC_API_KEY` un pakotne `anthropic`; citādi imitācija pēc atslēgvārdiem |
| Kad teksts tiek nosūtīts ārēji | ✅ Tikai pēc pogas; formā brīdinājums. Imitācijas režīmā rakstīts, ka teksts netiek sūtīts ārpus sistēmas |
| Rezultāts | ✅ Ne vairāk kā 3 teikumi + nākamais solis |
| Marķējums | ✅ Formā "Ģenerēts ar MI (Claude/imitācija)", kartītē "Ģenerēts ar MI · apstiprināja …" |
| Cilvēka kontrole | ✅ Kopsavilkums tiek ielikts formā rediģēšanai; saglabājas tikai pēc "Apstiprināt un saglabāt". Brīvās piezīmes netiek saglabātas |
| Žurnāls | ✅ `ai_generate` (kurš, kad) un `ai_approve` (kurš apstiprināja); avots mijiedarbības ierakstā; teksts netiek žurnalēts |
| Kļūdas | ✅ Noildze 10 s, API kļūda vai atteikums → automātiski imitācija, avots redzams marķējumā; lietotājs neredz 500 |
| Pārbaude | 🟡 Claude ceļš testēts ar aizstājēju; ar īstu API atslēgu nav pārbaudīts |

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
2. Galvenajā ceļā (pieslēgšanās → panelis → organizācija → mijiedarbība → pieprasījums → uzdevums) visu var izdarīt tikai ar tastatūru, un fokuss vienmēr ir redzams.
3. Lapas ir lietojamas 200 % mērogā un 320 px platumā bez horizontālas ritināšanas.
4. Ir skip-link, orientieri (`header`, `nav`, `main`, `footer`), loģiska virsrakstu secība un unikāli lapu virsraksti.
5. Statusi un kavējumi ir izteikti ar tekstu, ne tikai ar krāsu. Kontrasts ≥ 4.5:1.
6. Manuāls tests ar NVDA galvenajā ceļā. Rezultāti tiek ierakstīti F8 lapā.

### N2 · Personas dati (VDAR)

**Statuss: ✅ DONE (6 no 6).** Zari `crm-2-kontakti` … `crm-5-meklesana-parskats`. Testi: `tests/test_contacts.py`, `tests/test_interactions.py`, `tests/test_search_report.py`.

| # | Kritērijs | Statuss |
|---|---|---|
| 1 | **Minimizācija:** tikai F2 lauki, bez brīva teksta laukiem par personu. Meklēšana nemeklē mijiedarbību tekstā | ✅ DONE: forma bez brīva teksta par personu; meklēšana nemeklē mijiedarbībās un nerāda kontaktinformāciju |
| 2 | **Glabāšanas termiņš:** 3 gadi pēc pēdējās mijiedarbības (F2) | ✅ DONE (pārrēķins pēc mijiedarbības ar F3) |
| 3 | **Pēc termiņa beigām** kontakts nonāk sarakstā "Jāpārskata". Atbildīgais darbinieks vai vadītājs to pagarina (ar pamatojumu, kas tiek ierakstīts žurnālā) vai dzēš. Automātiskas dzēšanas nav | ✅ DONE: `/kontakti/japarskata`; pirms dzēšanas apstiprinājuma lapa |
| 4 | **Piekļuves žurnāls:** katra organizācijas vai kontaktpersonas kartītes atvēršana tiek ierakstīta (kas, ko, kad, darbība). Žurnālu var skatīt tikai administrators | ✅ DONE: `/zurnals` |
| 5 | **Dzēšana pēc pieprasījuma** (veic administrators): ieraksts dzēsts neatgriezeniski; mijiedarbībās "Dzēsta kontaktpersona"; žurnālā fakts bez personas datiem | ✅ DONE: darbinieks reģistrē pieprasījumu kontakta kartītē, administrators izpilda (ar apstiprinājumu) vai noraida; mijiedarbībās "Dzēsta kontaktpersona" |
| 6 | Lietotnes žurnālā (`logging`) netiek rakstīti personas dati un mijiedarbību teksti | ✅ DONE |

### N3 · Lomas

Skatīt 3. nodaļu.

### N4 · Tehnoloģijas un laiks

Skatīt 2. nodaļu.

## 7. Datu modelis (aptuvens)

| Tabula | Galvenie lauki |
|---|---|
| `lietotaji` | id, vārds, epasts (unikāls), paroles_jaucējvērtība, loma (`darbinieks` / `vaditajs` / `administrators` / NULL = gaida apstiprinājumu), aktīvs |
| `sesijas` | marķiera_jaucējvērtība, lietotajs_id, derīga_līdz |
| `organizacijas` | id, nosaukums, reg_nr (unikāls), veids, atbildigais_id |
| `kontakti` | id, organizacija_id, vārds, amats, epasts, talrunis, sazinas_pamats, pamata_datums, glabat_lidz |
| `mijiedarbibas` | id, organizacija_id, veids, datums, kopsavilkums, nakamais_solis, mi_generets, apstiprinaja_id, izveidoja_id |
| `mijiedarbibu_dalibnieki` | mijiedarbiba_id, kontakts_id (NULL, ja dzēsts) / lietotajs_id |
| `pieprasijumi` | id, organizacija_id, temats, apraksts, sanemts, termins, statuss |
| `uzdevumi` | id, apraksts, izpilditajs_id, izveidoja_id, datums, organizacija_id / pieprasijums_id, izpildits_laiks |
| `piekluves_zurnals` | id, lietotajs_id, darbiba, objekta_tips, objekta_id, laiks |

## 8. Ekrāni (9 + pieslēgšanās)

0. Pieslēgšanās un reģistrācija (F0)
1. Vadības panelis (F9)
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

Apjoms ir viss F0–F9 + MI-1. Ja laiks beidzas, secība ir:

1. Pamats: `base.html` (N1), F0 pārnešana uz Flask un lomas (N3), sākumdati
2. F9 vadības panelis (sākumā ar tiem blokiem, kuru dati jau ir)
3. F1 → F2 → F3 (ar piekļuves žurnālu, N2)
4. F4 → F5
5. F6 → F7
6. MI-1 (vispirms imitācija, tad Claude API)
7. F8 ar reāliem atradumiem, administratora ekrāni, "Jāpārskata" saraksts

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
| ~~8~~ | ~~F0 ir īstenots ar FastAPI, bet N4 prasa Flask~~ | **Atrisināts:** pārnests uz Flask (sk. lēmumu žurnālu) |
| 9 | Vai reģistrēties var jebkurš, vai kontus izveido tikai administrators? | Reģistrēties var jebkurš, bet bez lomas CRM datus neredz (N3) |
| 10 | Vai vajag paroles atjaunošanu un pieslēgšanās mēģinājumu ierobežošanu? | Ārpus apjoma prototipā, obligāti ražošanā |

## 11. Ārpus apjoma

- SSO, divfaktoru autentifikācija, paroles atjaunošana pa e-pastu
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
| Pieslēgšanās | ~~Lomas izvēle bez parolēm (mācību režīms)~~ → aizstāts | Produkta īpašnieks, 2026-10-14 |
| Pieslēgšanās (F0) | E-pasts + parole, kā īstenots CR-4; lomu piešķir administrators | Produkta īpašnieks, 2026-10-14 |
| Vadības panelis (F9) | Uzdevumi šodien, kavētie un tuvojošies pieprasījumi, pēdējās mijiedarbības, kopsavilkuma skaitļi | Produkta īpašnieks, 2026-10-14 |
| Apjoms 1,5 h | Viss F1–F8 + MI-1 (pēc tam papildināts ar F0 un F9) | Produkta īpašnieks, 2026-10-14 |
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
| Tehnoloģija (N4) | Lietotni pārnest no FastAPI uz Flask + Jinja2 atbilstoši prasībām; JSON API saglabāt | Produkta īpašnieks, 2026-10-14 |
