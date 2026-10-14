# CRM realizācijas plāns

> Versija 1.0 · 2026-10-14 · Saistītie dokumenti: [prasību saraksts](prasibu-saraksts.md) ·
> [ekrānu karte](ekranu-karte.md) · [vadības panelis](vadibas-panelis.md)

## 1. Kur esam

| Gatavs ✅ | Daļēji 🟡 | Vēl nav ⬜ |
|---|---|---|
| F0 Pieslēgšanās un lomas · F1 Organizācijas | F9 Panelis (3/7) · N2 Personas dati · N3 Lomas · N4 Tehnoloģijas | F2 · F3 · F4 · F5 · F6 · F7 · F8 · MI-1 · MI-2 · N1 |

Lietotne: Flask + Jinja2 + SQLite, 68 automātiskie testi, 11 gatavi ekrāni no 24 (sk. ekrānu karti).

## 2. Darba kārtība katrā posmā

1. Īstenoju posma prasības. Katrai prasībai ir savi testi pēc pieņemšanas kritērijiem.
2. Palaižu `make test` (un `make lint-contract`, ja mainās `docs/openapi.yaml`).
3. Atjaunoju statusu [prasību sarakstā](prasibu-saraksts.md), [ekrānu kartē](ekranu-karte.md) un attēlā (`make ekranu-karte`).
4. Komits katrai prasībai, ziņojums sākas ar ID (piem., `F2: kontaktpersonas`).
5. **Apstāšanās punkts:** jūs pārbaudāt pārlūkā un sakāt, kas jāmaina. Tikai tad sākas nākamais posms.

## 3. Posmi

### 2. posms · Kontaktpersonas un personas dati

| | |
|---|---|
| **Prasības** | F2, N2 (pabeigt) |
| **Ekrāni** | Kontaktpersonas forma (pievienot / labot) · Kontakti "Jāpārskata" · Dzēšanas pieprasījumi (administratoram) |
| **Galvenais** | Tikai nepieciešamie lauki · e-pasts vai tālrunis obligāts · "Glabāt līdz" = pēdējā mijiedarbība + 3 gadi, aprēķina automātiski · pagarināšana ar pamatojumu · dzēšana: kontakts dzēsts, mijiedarbībās "Dzēsta kontaktpersona" · kontakta kartītes atvēršana žurnālā |
| **F9 ieguvums** | Karte "kontakti jāpārskata" kļūst par saiti |
| **Jūs pārbaudāt** | Pievienot kontaktu Annas organizācijai, atrast to "Jāpārskata" sarakstā, administratoram izdzēst kontaktu pēc pieprasījuma |
| **Pieņēmumi** | Tālrunis `+371` + 8 cipari vai 8 cipari · pagarinājuma pamatojums līdz 200 rakstzīmēm · žurnāls glabājas 1 gadu |

### 3. posms · Mijiedarbības un MI-1

| | |
|---|---|
| **Prasības** | F3, MI-1 |
| **Ekrāni** | Mijiedarbības forma organizācijas kartītē, poga "Izveidot kopsavilkumu ar MI" |
| **Galvenais** | Veids, datums (ne nākotnē), dalībnieki (kontakti + darbinieki), kopsavilkums, nākamais solis · `app/ai.py`: `kopsavilkums(teksts)` → 3 teikumi + nākamais solis · imitācija pēc atslēgvārdiem, Claude API, ja ir `ANTHROPIC_API_KEY` · brīdinājums pirms sūtīšanas · marķējums "Ģenerēts ar MI" · darbinieks rediģē un apstiprina · žurnālā kurš, kad, avots, bez teksta · noildze 10 s → imitācija |
| **F9 ieguvums** | "Pēdējās mijiedarbības" ved uz organizācijas kartīti |
| **Jūs pārbaudāt** | Ierakstīt sanāksmi ar MI kopsavilkumu, labot to un saglabāt |
| **Lēmums no jums** | Vai būs Claude API atslēga? Ja nē, MI-1 strādās ar imitāciju, un tas atbilst prasībai |

### 4. posms · Pieprasījumi un uzdevumi

| | |
|---|---|
| **Prasības** | F4, F5 |
| **Ekrāni** | Pieprasījuma forma · Pieprasījumu saraksts (filtri: statuss, kavēti) · Uzdevuma forma · Mani uzdevumi šodien |
| **Galvenais** | Statuss tikai uz priekšu: Jauns → Darbā → Atbildēts · termiņš +1 mēnesis, var mainīt · "KAVĒTS (N d.)" tekstā · uzdevums sev vai kolēģim, saistīts ar organizāciju vai pieprasījumu · "Izpildīts" ar vienu pogu |
| **F9 ieguvums** | Saites "Skatīt visus" un no kartēm uz sarakstiem. **F9 kļūst ✅ (izņemot saiti uz F7)** |
| **Jūs pārbaudāt** | Izveidot pieprasījumu, pārvietot statusu, uzdot kolēģim uzdevumu un pārbaudīt, ka tas parādās viņa panelī |

### 5. posms · Meklēšana un vadītāja pārskats

| | |
|---|---|
| **Prasības** | F6, F7, F9 (pabeigt) |
| **Ekrāni** | Meklēšanas lauks galvenē + rezultātu lapa · Vadītāja pārskats |
| **Galvenais** | Meklē organizācijās, kontaktos, pieprasījumos, bet ne mijiedarbību tekstā · vismaz 2 rakstzīmes · rezultāti tabulās pa veidiem · pārskats: periods 7/30/90 d., aktivitāte pa darbiniekiem, kavētie pieprasījumi, top 5 organizācijas · diagramma servera pusē (SVG, bez JS) + tā pati tabula · tikai vadītājam |
| **F9 ieguvums** | Vadītājam saite "Atvērt pilno pārskatu". **F9 kļūst ✅** |
| **Jūs pārbaudāt** | Atrast organizāciju pēc daļas nosaukuma; vadītājam pārslēgt periodu |

### 6. posms · Piekļūstamība un kvalitāte

| | |
|---|---|
| **Prasības** | N1, F8, MI-2, N3 (pabeigt) |
| **Rezultāts** | `tests/a11y_check.py` (axe-core + Playwright) uz visiem galvenajiem ekrāniem, mērķis 0 critical/serious · automātiska pārbaude 320 px un 200 % · lapa `/pieklustamiba` ar **reāliem** atradumiem · `docs/mi2-klasifikacija.md` (kas tiek vērtēts, sekas, MI akta riska klase, lēmums "nebūvēt") · N3 tiesību matricas pilna pārbaude testos |
| **Jūs pārbaudāt** | Galveno ceļu tikai ar tastatūru; ja ir Windows, ar NVDA. Rezultātu ierakstām F8 lapā |

### 7. posms · Noslēgums

| | |
|---|---|
| **Rezultāts** | Visi statusi ✅ vai pamatoti 🟡 · atjaunota ekrānu karte · README ar palaišanas instrukciju · PR uz `main` |
| **Jums jāizdara** | `setup/claude-answer.md` (A0, bez tā CI neiziet) · `tracker/CR-4.md` (projekta noteikumi) |

## 4. Git un pull request

Šobrīd viss darbs ir ķēdē `cr-4-auth` → `f9-panelis` → `n4-flask` → `f0-lomas`. Zars `f0-lomas` satur visu. Nosūtīts uz GitHub ir tikai `crm-prasibas`.

**Ieteikums:**
1. Pēc 1. posma pārbaudes nosūtu `f0-lomas` uz GitHub un izveidoju **vienu PR uz `main`** ("CRM 1. posms: F0, F1, F9, N4").
2. Katram nākamajam posmam ir savs zars no `main` (`crm-2-kontakti`, `crm-3-mijiedarbibas`, …) un savs PR. Tā katru posmu var pārskatīt atsevišķi.

## 5. Riski

| Risks | Ko darām |
|---|---|
| Lapas pārbaudītas tikai ar testiem, ne ar acīm | Apstāšanās punkts pēc katra posma; 6. posmā automātiski ekrānuzņēmumi un axe |
| Codespace dzēšana, lokālie zari pazūd | Nosūtīt zarus uz GitHub pēc katra posma |
| Playwright un Flask nav kursa vides attēlā | Flask ir `requirements.txt` un `postCreateCommand`; Playwright instrukcija `ekranu-karte.md` |
| MI-1 sūta tekstu ārējam pakalpojumam (VDAR) | Tikai pēc pogas, ar brīdinājumu; bez atslēgas strādā imitācija |
| Atvērtie jautājumi (prasību saraksta 10. nodaļa) | Strādājam pēc ierakstītajiem pieņēmumiem; ja atbilde mainās, labojam |
