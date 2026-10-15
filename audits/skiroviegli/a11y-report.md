# Piekļūstamības pārbaude · www.skiroviegli.lv

> Pārbaudīts 15.10.2026 · axe-core 4.12.1 (Playwright, Chromium) · WCAG 2.0/2.1/2.2 A un AA
> Vietnes uzturētājs: **Valsts vides dienests** (iestāde) → piemērojami MK 14.07.2020. noteikumi Nr. 445 un EN 301 549.
> Neatkarīgs automātisks audits ar papildu pārbaudēm; nav aizstājējs pilnam izvērtējumam ar ekrānlasītāju.
> Neapstrādātie dati: [axe-rezultati.json](axe-rezultati.json) · skripts: [audit.py](audit.py)

## 1. Kopsavilkums

| | Rezultāts |
|---|---|
| axe pārkāpumi (unikāli noteikumi) | **5**: 2 kritiski (`image-alt`, `label`), 2 nopietni (`color-contrast`, `html-has-lang`); `label` tikai atvērtā filtrā |
| Ietekmēti elementi | 114 attēli bez alt teksta, 9–15 teksta elementi ar nepietiekamu kontrastu, 1 lauks bez etiķetes, `<html>` bez valodas |
| Papildu atradumi (pārbaudīti skriptā, ārpus axe) | 320 px platumā horizontāla ritināšana (+45 px); nav orientieru un "Pāriet uz saturu"; 4 h1, viens ar tekstu "LEAFLET-SIDEBAR"; dialogiem nav nosaukuma; 115 marķieri ar vienādu nosaukumu "Marker" |
| Kas strādā labi | Fokuss redzams visiem pārbaudītajiem elementiem (25 Tab pieturas); dialoglodziņi pārvieto fokusu uz sevi un notur to iekšā; 640 px (200 % mērogs) bez ritināšanas; tulkotāja izvēlnei ir nosaukums |
| Piekļūstamības paziņojums | **Ir**, bet **neatbilst pilnībā** MK 445 / ES parauga prasībām: saite uz izvērtēšanas protokolu ir salauzta (404), un paziņojumā nav uzskaitīts nepiekļūstamais saturs, datums un sūdzību kārtība (sk. 4. nodaļu) |

## 2. Pārbaudītās lapas

Vietne ir vienas lapas lietotne: visa informācija ir adresē `https://www.skiroviegli.lv/`, papildu saturs atveras dialoglodziņos.
Tāpēc tika pārbaudīti pieci **lapas stāvokļi**:

| # | Lapa / stāvoklis | Kā atvērts |
|---|---|---|
| 1 | Sākumlapa (1280 px) | `https://www.skiroviegli.lv/` |
| 2 | Piekļūstamības paziņojums | Izvēlne «Piekļūstamība» → dialogs `#accessibilityModal` |
| 3 | Informācija operatoriem | Izvēlne «Informācija operatoriem» → dialogs `#infoForOperatorsModal` |
| 4 | Karte ar atvērtu pašvaldību filtru | Poga «Visa Latvija» |
| 5 | Sākumlapa 320 px platumā | Mobilā skata platums (WCAG 1.4.10) |

## 3. Atradumi

Smagums: axe vērtējums (**kritisks / nopietns / vidējs / zems**); rindām ar "(manuāls)" smagumu novērtēja auditors, jo axe tās neatzīmē automātiski.

| # | Lapa | Problēma | WCAG kritērijs | Smagums | Ieteiktais labojums |
|---|---|---|---|---|---|
| 1 | Visas (1–5) | `<html>` elementam nav `lang` atribūta — ekrānlasītājs var lasīt latviešu tekstu ar nepareizu izrunu | 3.1.1 Lapas valoda (A) | Nopietns | `<html lang="lv">`. Google tulkotājs pēc tulkošanas atribūtu nomaina pats |
| 2 | 1–5 (karte) | 114 kartes kopu ikonām (`.leaflet-marker-icon > figure > img`) nav `alt` atribūta | 1.1.1 Ne-teksta saturs (A) | Kritisks | Ikonām `alt=""` (dekoratīvas), bet kopas elementam pieejams nosaukums ar skaitu, piem. `aria-label="17 pieņemšanas vietas — tuvināt"` |
| 3 | 1–5 (karte) | Visiem 115 marķieriem `alt="Marker"` un `role="button"` — nosaukums nepasaka, kura vieta tā ir | 1.1.1 (A), 4.1.2 Nosaukums, loma, vērtība (A) | Nopietns (manuāls) | `alt`/`aria-label` ar vietas nosaukumu un veidu, piem. «Dalītās savākšanas punkts, Ezera iela 12» |
| 4 | 1 (karte) | Katrs no 115 marķieriem ir atsevišķa Tab pietura, un nav teksta saraksta alternatīvas — tastatūras lietotājam jāiziet simtiem pieturu bez iespējas izlaist karti | 2.1.1 Tastatūra (A), 2.4.1 Bloku apiešana (A) | Vidējs (manuāls) | Saite «Izlaist karti» pirms kartes; pieņemšanas vietu saraksts vai tabula ar tiem pašiem datiem un filtriem |
| 5 | 1–3, 5 (augšējā izvēlne) | Saites «Piekļūstamība», «Informācija operatoriem»: #5e813c uz #e8e7e6 — **3,63:1** (vajag ≥ 4,5:1) | 1.4.3 Kontrasts (AA) | Nopietns | Tumšāks zaļais, piem. **#506e33** (4,7:1) |
| 6 | 1–3, 5 (apraksts, kontakti, «Pastāsti draugiem») | Pelēks teksts #7f7f7f uz #e8e7e6 — **3,24:1**; arī 11 px `<em>` | 1.4.3 Kontrasts (AA) | Nopietns | Teksta krāsa **#666666** (4,65:1) vai tumšāka; mazajam tekstam ≥ 4,5:1 obligāti |
| 7 | 4 (pašvaldību filtrs) | Meklēšanas laukam filtra izvēlnē nav etiķetes (tukšs `placeholder`) | 4.1.2 (A), 1.3.1 (A), 3.3.2 Etiķetes (A) | Kritisks | `<label>` vai `aria-label="Meklēt pašvaldību"` |
| 8 | 5 (320 px) | Reklāmkarogs «LIETOVELREIZ» (`/LV_ban_cut.png`, fiksēts augstums 80 px → 333 px plats) rada 45 px horizontālu ritināšanu | 1.4.10 Pārplūšana (AA) | Vidējs | `max-width: 100%; height: auto;` |
| 9 | Visas | Nav orientieru (`header`, `nav`, `main`, `footer` — 0) un nav «Pāriet uz saturu» saites | 1.3.1 (A), 2.4.1 Bloku apiešana (A) | Vidējs (manuāls) | Semantiski HTML5 elementi un skip-link kā pirmā Tab pietura. axe `bypass` neatzīmēja, jo lapā ir virsraksti |
| 10 | Visas | 4 `h1` virsraksti; viens no tiem ir tehnisks vietturis «LEAFLET-SIDEBAR» paslēptā sānjoslā, ko ekrānlasītājs nolasa | 1.3.1 (A), 2.4.6 Virsraksti un etiķetes (AA) | Vidējs (manuāls) | Viens `h1`, pārējie `h2`; sānjoslai īsts nosaukums vai `aria-hidden="true"`, kamēr tā ir aizvērta |
| 11 | 2, 3 (dialogi) | Dialogiem `role="dialog"` nav pieejama nosaukuma (`aria-labelledby` trūkst); aizvēršanas pogas nosaukums angliski «Close» | 4.1.2 (A), 3.1.2 Daļu valoda (AA) | Vidējs (manuāls) | `aria-labelledby` uz dialoga virsrakstu; pogai `aria-label="Aizvērt"` |
| 12 | 2 (paziņojums) | Sadaļu nosaukumi «Cik piekļūstama ir šī tīmekļvietne?» un «Atsauksmēm un saziņai» ir saites uz `#`, nevis virsraksti | 1.3.1 (A), 2.4.4 Saites mērķis (A) | Vidējs (manuāls) | `<h2>` elementi, bez saites |
| 13 | 2 (paziņojums) | Saite «Piekļūstamības izvērtēšanas protokols» atgriež **404** (pārbaudīts gan `skiroviegli.lv`, gan `www.`) | — (MK 445 paziņojuma saturs) | Augsts (atbilstība) | Publicēt protokolu vai nepiekļūstamo saturu uzskaitīt pašā paziņojumā (sk. 4. nodaļu) |
| 14 | 1–5 | axe «nepilnīgi»: `color-contrast` 121 elements (teksts uz attēliem/kartes), `target-size` 6 elementi | 1.4.3 (AA), 2.5.8 Mērķa izmērs (AA) | Jāpārbauda manuāli | Pārbaudīt ar krāsu pipeti un izmērīt mērķus (≥ 24×24 px) |

## 4. Piekļūstamības paziņojums pret MK noteikumiem Nr. 445

Paziņojums atrodas augšējā izvēlnē «Piekļūstamība» (dialoglodziņš, sasniedzams no sākumlapas). Salīdzinājums ar MK 445
un ES paziņojuma paraugu (Komisijas Īstenošanas lēmums (ES) 2018/1523), ko izmanto kā MK 445 paziņojuma struktūru:

| Prasītais elements | Paziņojumā | Vērtējums |
|---|---|---|
| Iestāde un atsauce uz MK 445 | «Valsts vides dienests saskaņā ar … noteikumiem Nr. 445» | ✅ |
| Tīmekļvietne, uz kuru attiecas | «https://skiroviegli.lv» | ✅ |
| Atbilstības statuss | «daļēji atbilst noteikumiem Nr. 445 turpmāk minēto iemeslu dēļ» | ✅ |
| **Nepiekļūstamais saturs un iemesli** (neatbilstība / nesamērīgs slogs / ārpus tvēruma) | Paziņojumā nav uzskaitīts; «turpmāk minētie iemesli» norāda tikai uz protokola PDF, **kas atgriež 404** | ❌ |
| Izvērtējuma metode | «vienkāršotais piekļūstamības izvērtējums», VARAM vadlīnijas | ✅ (ministrijas nosaukums norādīts vecajā redakcijā «Vides aizsardzības un reģionālās attīstības ministrija») |
| **Paziņojuma sagatavošanas un pārskatīšanas datums** | Nav | ❌ |
| Atgriezeniskā saite un kontakti | E-pasts, tālrunis, adrese; atbilde 7 dienu laikā | ✅ |
| Alternatīva nepiekļūstamajam saturam | «vēlaties saņemt nepiekļūstamo saturu citā formātā, sazinieties ar mums» | 🟡 vispārīgi, bez konkrētām alternatīvām |
| **Sūdzību / izpildes nodrošināšanas kārtība** (uzraugošā iestāde, Tiesībsargs) | Nav | ❌ |
| Paziņojums pats ir piekļūstams | Dialogs bez nosaukuma; sadaļu nosaukumi ir saites, nevis virsraksti (atradumi #11, #12) | 🟡 |

**Secinājums:** piekļūstamības paziņojums **ir publicēts un sasniedzams**, bet **neatbilst pilnībā** prasībām: tajā trūkst
nepiekļūstamā satura saraksta (protokola saite salauzta), sagatavošanas/pārskatīšanas datuma un sūdzību iesniegšanas kārtības.
Turklāt paziņojums apgalvo «daļēji atbilst», kamēr automātiskā pārbaude atrod 2 kritiskas kļūdas, kas paziņojumā nav minētas.

**Ieteikumi paziņojumam:**
1. Atjaunot protokola PDF vai ielikt nepiekļūstamā satura sarakstu tieši paziņojumā (piem., šīs atskaites #1–#12 ar labošanas termiņiem).
2. Pievienot «Sagatavots: [datums]» un «Pārskatīts: [datums]».
3. Pievienot sadaļu «Sūdzību iesniegšana»: ja atbilde nav saņemta vai neapmierina — uzraugošā iestāde, tālāk Tiesībsargs.
4. Atjaunināt ministrijas nosaukumu uz pašreizējo.
5. Paziņojumu publicēt arī ar savu adresi (piem., `/pieklustamiba`), lai uz to var dot saiti.

## 5. Ierobežojumi

- Automātiskā pārbaude atrod tikai daļu problēmu (tipiski 30–50 %). Ekrānlasītāja (NVDA/VoiceOver) un manuālā tastatūras pārbaude nav veikta.
- Pārbaudīts viens pārlūks (Chromium) un 5 stāvokļi; kartes saturs (OpenStreetMap flīzes) un Google tulkotājs ir trešo pušu komponenti.
- Juridiskie secinājumi par MK 445 balstīti uz ES paziņojuma paraugu; ieteicams salīdzināt ar MK 445 aktuālo redakciju un VARAM vadlīnijām.
- Audits tikai lasīja publisko vietni (viena caurlaide); nekas netika iesniegts vai mainīts.
