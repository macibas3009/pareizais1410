# Vadības panelis (F9) · apraksts

> Ezermalas novada pašvaldības CRM · mācību prototips · 2026-10-14
> Prasība: [prasibu-saraksts.md](prasibu-saraksts.md), sadaļa F9. Visi dati ir sintētiski.

## 1. Kam tas paredzēts

Vadības panelis ir pirmā lapa, ko lietotājs redz pēc pieslēgšanās. Tajā uzreiz redzams,
kas šodien jādara: kuri uzdevumi jāizpilda, kuri pieprasījumi kavējas vai drīz kavēsies
un kas pēdējā laikā noticis ar lietotāja organizācijām. Pilnie saraksti un pārskati ir
citās lapās (F3–F7). Panelis rāda tikai svarīgāko.

## 2. Kā atvērt

| Darbība | Rezultāts |
|---|---|
| Pieslēdzas lapā `/login` | Automātiski atveras `/panelis` |
| Atver `/panelis` bez pieslēgšanās | Novirza uz `/login` |
| Klikšķis uz zīmola vai "Sākums" augšējā joslā | Atveras `/panelis` |
| Vecā adrese `/profile` | Novirza uz `/panelis` |

Lokāli: `make install` (vienreiz), `make run`, tad http://localhost:8000/login. Codespace vidē: cilne **Ports** → ports 8000.

## 3. Ko redz katra loma

| Loma | Tvērums | Bloki |
|---|---|---|
| **Darbinieks** | Tikai organizācijas, kurās viņš ir atbildīgais darbinieks, un viņam piešķirtie uzdevumi | Kopsavilkums, Uzdevumi šodien, Kavētie un tuvojošies pieprasījumi, Pēdējās mijiedarbības |
| **Vadītājs** | Visa iestāde: visas organizācijas, visu darbinieku uzdevumi | Tie paši bloki; uzdevumiem papildus redzams izpildītājs |
| **Administrators** | Lietotāju pārvaldība, ne CRM dati | Lietotāji, kas gaida lomu |
| **Bez lomas** (jauns reģistrēts konts) | Nekādi CRM dati | Paziņojums "Konts gaida apstiprinājumu" |

Loma tiek nolasīta no datubāzes katrā pieprasījumā. Ja lomu maina, izmaiņa redzama nākamajā lapas atvēršanā, un no jauna pieslēgties nevajag.

## 4. Izkārtojums

```
┌──────────────────────────────────────────────────────────────────────────┐
│ ◉ Ezermalas novada pašvaldība   Sākums           Anna Kalniņa   [Iziet]  │
│   Pieteikumu sistēma                             Darbinieks              │
├──────────────────────────────────────────────────────────────────────────┤
│ ┌──────────────────────────────────────────────────────────────────────┐ │
│ │ (ezera fotogrāfija)                                                  │ │
│ │ Trešdiena, 2026. gada 14. oktobris                                   │ │
│ │ Labdien, Anna!                                                       │ │
│ │ Jūsu organizācijas, uzdevumi un termiņi                              │ │
│ └──────────────────────────────────────────────────────────────────────┘ │
│ ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐              │
│ │ 4          │ │ 5          │ │ 3          │ │ 2          │              │
│ │ manas      │ │ atvērti    │ │ uzdevumi   │ │ kontakti   │              │
│ │ organizāc. │ │ pieprasīj. │ │ šodien     │ │ jāpārskata │              │
│ └────────────┘ └────────────┘ └────────────┘ └────────────┘              │
│ ┌──────────────────────────────┐ ┌─────────────────────────────────────┐ │
│ │ Uzdevumi šodien              │ │ Kavētie un tuvojošies pieprasījumi  │ │
│ │ [Nokavēts] Nosūtīt ...  [✓]  │ │ Temats  Organizācija  Statuss  Term.│ │
│ │ [Šodien]   Piezvanīt... [✓]  │ │ ...     ...           Darbā  KAVĒTS │ │
│ └──────────────────────────────┘ └─────────────────────────────────────┘ │
│ ┌──────────────────────────────────────────────────────────────────────┐ │
│ │ Pēdējās mijiedarbības                                                │ │
│ │ 14.10.2026 · Sanāksme   SIA Ezerkrasta Būve   Apspriests kopīgs ...  │ │
│ └──────────────────────────────────────────────────────────────────────┘ │
├──────────────────────────────────────────────────────────────────────────┤
│ © Ezermalas novada pašvaldība · mācību prototips · Foto: ... CC BY-SA 4.0│
└──────────────────────────────────────────────────────────────────────────┘
```

Ja ekrāns ir šaurāks par 860 px, bloki izkārtojas vienā kolonnā, un mijiedarbību rindas sadalās vairākās rindiņās.

## 5. Bloki un aprēķinu noteikumi

"Manas" nozīmē: darbiniekam tās ir organizācijas, kurās viņš ir atbildīgais. Vadītājam tās ir visas organizācijas.
"Šodiena" ir servera datums.

### 5.1. Kopsavilkuma kartes

| Karte | Kā aprēķina | Izcelta (oranža mala), ja |
|---|---|---|
| **Organizācijas** | Manu organizāciju skaits. Vadītājam: "organizācijas iestādē" | nekad |
| **Atvērti pieprasījumi** | Manu organizāciju pieprasījumi ar statusu `Jauns` vai `Darbā` | nekad |
| **Uzdevumi šodien** | Man piešķirtie neizpildītie uzdevumi ar termiņu **šodien vai agrāk** (arī nokavētie). Vadītājam: visu darbinieku | skaits > 0 |
| **Kontakti jāpārskata** | Manu organizāciju kontaktpersonas, kuru "Glabāt līdz" datums ir pagājis (N2). Saite uz `/kontakti/japarskata` | skaits > 0 |

Teksts tiek locīts pēc skaitļa: "1 atvērts pieprasījums", "5 atvērti pieprasījumi", "21 atvērts pieprasījums".
Krāsa ir tikai papildu norāde. Nozīme vienmēr ir saprotama no teksta.

### 5.2. Uzdevumi šodien

- Rāda ne vairāk kā **5** uzdevumus: neizpildītus, ar termiņu šodien vai agrāk, kārtotus pēc termiņa (vecākie augšā).
- Atzīme pie katra uzdevuma: **Nokavēts** (sarkana), ja termiņš ir pagājis, vai **Šodien** (dzeltena).
- Zem apraksta ir organizācija. Vadītājam redzams arī izpildītāja vārds.
- Poga **Izpildīts** atzīmē uzdevumu kā izpildītu un atjauno paneli. Darbinieks to var tikai saviem uzdevumiem, vadītājs jebkuram. Ekrāna lasītājs nolasa "Izpildīts: <uzdevuma apraksts>".
- Ja uzdevumu nav: "Šodien uzdevumu nav."

### 5.3. Kavētie un tuvojošies pieprasījumi

- Tabula ar kolonnām: Temats, Organizācija, Statuss, Termiņš.
- Rāda manu organizāciju pieprasījumus ar statusu `Jauns` vai `Darbā`, kuru termiņš ir **pagājis vai būs nākamajās 7 dienās**. Kārtoti pēc termiņa, bez skaita ierobežojuma.
- Termiņa teksts:

  | Situācija | Teksts | Krāsa |
  |---|---|---|
  | Termiņš pagājis pirms N dienām | `KAVĒTS (N d.)` | sarkana |
  | Termiņš šodien | `Termiņš šodien` | dzeltena |
  | Termiņš pēc N dienām (1–7) | `Termiņš pēc N d.` | zila |

  Blakus ir datums formātā `dd.mm.gggg`.
- Ja nav neviena: "Kavētu vai tuvojošos pieprasījumu nav."

### 5.4. Pēdējās mijiedarbības

- **5** jaunākās manu organizāciju mijiedarbības (zvans, e-pasts, sanāksme), jaunākā augšā.
- Katrā rindā: datums un veids, organizācija, kopsavilkuma **pirmais teikums**. Pilns teksts ir organizācijas kartītē (F1/F3).
- Ja nav: "Mijiedarbību vēl nav."

### 5.5. Administratora panelis

- Kartes: cik lietotāju gaida lomu un cik dzēšanas pieprasījumu gaida (abas ir saites).
- Tabula "Lietotāji, kas gaida lomu": vārds, e-pasts, **pieprasītā loma**, reģistrācijas datums un darbības:
  - **Apstiprināt**: piešķir pieprasīto lomu ar vienu klikšķi;
  - **Cita loma**: atver lapu `/lietotaji`, kur var izvēlēties citu lomu;
  - **Noraidīt**: dzēš kontu, kas vēl nav apstiprināts.
- Saites uz lapām "Visi lietotāji un lomas" (`/lietotaji`), "Dzēšanas pieprasījumi" (`/dzesanas-pieprasijumi`) un "Piekļuves žurnāls" (`/zurnals`).
- Visas lomu izmaiņas tiek ierakstītas piekļuves žurnālā. Savu lomu administrators mainīt nevar.

## 6. Piekļūstamība (N1)

- Lapa ir renderēta servera pusē un strādā **bez JavaScript**. Poga "Izpildīts" un "Iziet" ir parastas formas (POST → redirect → GET).
- Pirmā saite lapā ir **"Pāriet uz saturu"**, kas redzama, kad uz tās nonāk ar Tab.
- Orientieri: `header`, `nav` ("Galvenā navigācija"), `main`, `footer`. Virsrakstu secība: `h1` sveiciens, `h2` katram blokam.
- Tabulām ir `<caption>` un `<th scope>`. Pieprasījuma temats ir rindas virsraksts.
- Statusi ir izteikti ar tekstu ("KAVĒTS (3 d.)", "Nokavēts"), ne tikai ar krāsu.
- Fokuss ir redzams (zila kontūra). Visas darbības var izdarīt ar tastatūru.

## 7. Personas dati (N2)

- Panelī ir tikai organizāciju nosaukumi, darbinieku vārdi un mijiedarbību pirmais teikums. Kontaktpersonu vārdi un e-pasti panelī netiek rādīti, ir tikai to skaits kartē "jāpārskata".
- Paneļa atvēršana netiek ierakstīta piekļuves žurnālā. Žurnālā tiek ierakstīta organizācijas kartītes atvēršana (F1), ko administrators redz lapā `/zurnals`.
- Lietotnes žurnālā netiek rakstīti personas dati.

## 8. Testa lietotāji un lomu piešķiršana

### Testa lietotāji

Tos izveido komanda `make seed`. Darba datubāzē `data/app.db` tie jau ir.

| E-pasts | Vārds | Loma | Ko redz |
|---|---|---|---|
| `darbinieks@example.com` | Anna Kalniņa | darbinieks | 4 organizācijas, savus uzdevumus |
| `darbinieks2@example.com` | Mārtiņš Ozols | darbinieks | 4 citas organizācijas |
| `vaditajs@example.com` | Ilze Bērziņa | vadītājs | Visu iestādi (10 organizācijas) |
| `admin@example.com` | Kārlis Liepa | administrators | Lietotājus, kas gaida lomu |

Parole visiem: `Ezermala-2026!`. Citu paroli var uzdot ar vides mainīgo `SEED_PASSWORD` pirms `make seed`.
Šie konti ir tikai lokālai mācību videi.

### Lomas piešķiršana jaunam lietotājam

1. Lietotājs reģistrējas lapā `/register` un izvēlas, kādu lomu pieprasa: **Darbinieks** vai **Vadītājs**.
2. Pēc pieslēgšanās viņš redz "Konts gaida apstiprinājumu" un pieprasīto lomu.
3. Administrators (`admin@example.com`) savā panelī redz pieprasījumu un nospiež **Apstiprināt**. Ja vajag citu lomu, izmanto **Cita loma**.
4. Lietotājs atsvaidzina lapu un redz savu paneli. No jauna pieslēgties nevajag.

Rezerves variants terminālī, piemēram, ja nav neviena administratora:
```bash
make users
make role EMAIL=vards@example.com ROLE=administrators
```

Jaunam darbiniekam sākumā nav organizāciju, tāpēc viņa panelī būs nulles. Vadītājs var viņu norādīt kā atbildīgo organizācijas labošanas formā (F1).

## 9. Tehniskā informācija

| Daļa | Fails |
|---|---|
| Lietotne (Flask) un maršruti `/panelis`, `/uzdevumi/<id>/izpildits`, `/iziet` | `app/main.py` |
| Vaicājumi un formatēšana | `app/dashboard.py` |
| HTML (Jinja2) | `app/templates/panelis.html`, `base.html` |
| Datubāzes tabulas | `app/db.py` |
| Sākumdati | `app/seed.py` |
| Lomu komanda | `app/roles.py` |
| Stils | `app/static/style.css` (sadaļa "F9") |
| Testi | `tests/test_dashboard.py` |

## 10. Zināmie ierobežojumi

| Trūkst | Kāpēc | Kad būs |
|---|---|---|
| Saites "Skatīt visus" un no kartēm "atvērti pieprasījumi", "uzdevumi šodien" | Sarakstu lapas vēl nav | F4, F5 |
| Vadītājam saite "Atvērt pilno pārskatu" | Pārskata vēl nav | F7 |
| 320 px izkārtojums | Uzrakstīts, bet nav pārbaudīts pārlūkā | N1 testi |
