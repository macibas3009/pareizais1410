# MI riska novērtējums · «Iesniegumi»

> 2026-10-14 · Pēc veidnes [MI-RISKA-KLASIFIKACIJA.md](MI-RISKA-KLASIFIKACIJA.md) (MI akts — Regula (ES) 2024/1689, pēc "Digitālā omnibusa").
> Sagatavoja: Claude Code (melnraksts) · **Apstiprina: atbildīgā persona un jurists** (sk. katra komponenta pēdējo rindu).
> Klasificēts **pirms** būvēšanas; US-7 pasākumi pēc īstenošanas pārbaudīti (sk. 5. nodaļu).

## 1. Kopsavilkums

| Komponents | Vai MI sistēma? | Riska klase | Lēmums | Termiņš |
|---|---|---|---|---|
| **US-7** MI ieteikums darbiniekam (tēma + atbildes projekts) | Ar Claude API — jā; imitācija — nē | **Minimāls** (ar labās prakses caurspīdīgumu) | Būvēt, ar cilvēka uzraudzību | Labā prakse tagad; 50. p. no 02.08.2026, ja atbildes publicētu bez cilvēka |
| **US-10** Čata palīgs iedzīvotājam | Jā (LLM) | **Ierobežots** (50. p. 1. d. caurspīdīgums) | Nebūvēt šajā posmā (COULD); ja būvē — tikai ar pasākumiem zemāk | 02.08.2026 |
| **US-15** "Prioritātes vērtējums" sociālajai palīdzībai | Jā (vērtēšanas modelis / LLM) | **Augsts** (III pielikums 5.a; profilēšana); robeža ar aizliegto praksi jāpārbauda | **Nebūvēt.** Alternatīva bez MI | 02.12.2027 (augsta riska prasības) |

## 2. US-7 · MI ieteikums darbiniekam

| Lauks | Atbilde |
|---|---|
| Komponenta nosaukums | US-7 "MI ieteikums": `ai.ieteikums(apraksts) -> {tema, atbildes_projekts}` |
| Mērķis (ko dara, kam) | Darbiniekam iesaka iesnieguma tēmu (viena no 6) un sagatavo atbildes projektu, lai ātrāk atbildētu |
| Ievade → izvade | Iesnieguma apraksts (brīvs teksts, var saturēt personas datus) → tēma + atbildes teksta projekts |
| Vai MI sistēma (3. p. 1. pkt.)? Kāpēc? | **Ar Claude API — jā**: LLM no ievades secina un ģenerē saturu ar autonomiju. **Atslēgvārdu imitācija (noklusējums) — nē**: deterministiski `if/else` noteikumi. Projektējam tā, it kā tā vienmēr būtu MI sistēma |
| Mūsu loma | Integrējam GPAI modeli (Claude) savā sistēmā ar savu mērķi → **nodrošinātājs** (izstrādājam sistēmu) un **uzturētājs** (iestāde lieto). Modeļa nodrošinātājs ir Anthropic (GPAI pienākumi — tam) |
| Kas pieņem gala lēmumu? Vai cilvēks var neņemt vērā? | **Darbinieks.** Ieteikums tikai parādīts; projekts nonāk atbildes laukā tikai pēc pogas "Izmantot projektu", tur to rediģē; statusu "Atbildēts" un tekstu apstiprina darbinieks. Tēmu MI nemaina automātiski. Ieteikumu var ignorēt |
| Ietekme uz personu | Netieša: ātrāka, vienveidīgāka atbilde. Riski: kļūdains projekts nokopēts bez lasīšanas; nepareiza tēma → iesniegums nonāk citā rindā; iesnieguma teksts ar personas datiem tiek sūtīts API (ja ieslēgts) |
| Aizliegta prakse (5. p.)? | ☑ Nē — nav manipulācijas, sociālās vērtēšanas, emociju atpazīšanas, biometrijas |
| III pielikuma joma? Kura? | ☑ Nē — tēmu šķirošana un teksta projekts nevērtē atbilstību pabalstam (5.a). **Uzmanību:** ja tēma "Sociālā palīdzība" ietekmētu, *vai* vai *cik ātri* iesniegums tiek izskatīts, jāpārvērtē |
| 6. p. 3. d. izņēmums? Profilēšana? | Pat ja uzskatītu par III pielikuma jomu: a) šaurs procedūras uzdevums un d) sagatavošanās uzdevums; **profilēšanas nav** (vērtē tekstu, ne personu) |
| Caurspīdīgums (50. p.)? | Teksts iekšējai lietošanai; atbildi pirms nosūtīšanas rediģē un apstiprina cilvēks → redakcionāla atbildība, 50. p. 4. d. publicēšanas pienākums nav piemērojams. Tomēr **marķējam UI** (50. p. gars) |
| **Riska klase** | ☐ Aizliegts ☐ Augsts ☐ Ierobežots ☑ **Minimāls** (ar brīvprātīgu caurspīdīgumu) |
| Piemērojamie pienākumi | Labā prakse (95. p. rīcības kodeksi); GPAI nodrošinātāja lietošanas noteikumi; **VDAR**: iesnieguma teksts uz ārēju API — apstrādes līgums ar nodrošinātāju, minimizācija, informācija privātuma paziņojumā; MI pratība darbiniekiem (4. p., ieteicama) |
| Termiņš | Labā prakse — no ieviešanas. 50. p. — no 02.08.2026 (attiektos, ja MI teksts tiktu publicēts bez cilvēka) |
| Pasākumi mūsu dizainā | Marķējums "Ģenerēts ar MI, pārbaudiet pirms lietošanas"; `<section aria-labelledby>`; obligāta rediģēšana — projekts nonāk laukā, nevis tiek nosūtīts; ieteikums **nekad nenosūta un nemaina statusu/tēmu automātiski**; `notikumi` ieraksts "MI ieteikums izmantots" un "Tēma mainīta pēc MI ieteikuma"; noklusēti imitācija bez tīkla; Claude tikai ar `ANTHROPIC_API_KEY`; teksts netiek rakstīts žurnālā; kvalitātes izlases pārbaude reizi mēnesī (organizatorisks) |
| Atlikušie jautājumi juristam | Vai iesnieguma teksta sūtīšanai uz GPAI API pietiek ar esošo privātuma paziņojumu? Kur glabājas dati (ES/ASV), datu apstrādes līgums? Vai sociālās palīdzības iesniegumiem MI ieteikumu vajadzētu izslēgt pavisam (piesardzība)? |

## 3. US-10 · Čata palīgs iedzīvotājam (netiek būvēts — COULD)

| Lauks | Atbilde |
|---|---|
| Komponenta nosaukums | US-10 čata palīgs: "Kā iesniegt? Kādi dokumenti vajadzīgi?" |
| Mērķis | Atbild iedzīvotājiem uz jautājumiem par iesniegšanu, termiņiem, dokumentiem |
| Ievade → izvade | Iedzīvotāja jautājums (brīvs teksts, var saturēt personas datus) → atbildes teksts |
| Vai MI sistēma? | **Jā** — LLM ģenerē saturu, mijiedarbojas ar cilvēku |
| Mūsu loma | Nodrošinātājs (izstrādājam uz GPAI bāzes) + uzturētājs (iestāde lieto) |
| Gala lēmums | Čats lēmumus nepieņem, bet iedzīvotājs **rīkojas pēc atbildes** (piem., neiesniedz dokumentu, nokavē termiņu). Cilvēks atbildi pirms parādīšanas nepārbauda |
| Ietekme uz personu | **Vidēja**: nepareiza juridiska informācija (termiņš, dokumenti, tiesības uz palīdzību) var atturēt no pakalpojuma vai pabalsta pieprasīšanas; uzticība iestādei; ievainojamas grupas (seniori, cilvēki krīzē) |
| Aizliegta prakse (5. p.)? | ☑ Nē — ja nav manipulatīvu tehniku un ievainojamību izmantošanas (5. p. 1. d. a, b). **Dizaina prasība:** nedrīkst atrunāt no iesnieguma iesniegšanas |
| III pielikuma joma? | ☑ Nē — sniedz vispārīgu informāciju, nevērtē atbilstību pabalstam (5.a). **Robeža:** ja čats sāk teikt "jums pabalsts nepienākas" → tuvojas 5.a; jāaizliedz dizainā |
| 6. p. 3. d.? Profilēšana? | Nav piemērojams (nav III pielikumā); profilēšanu neveic, sarunas netiek sasaistītas ar personu |
| Caurspīdīgums (50. p.)? | **Jā, 50. p. 1. d.**: lietotājs jāinformē, ka sarunājas ar MI sistēmu (skaidri, pirms pirmās atbildes). Ģenerētais teksts — mašīnlasāms marķējums (50. p. 2. d., nodrošinātājs) |
| **Riska klase** | ☐ Aizliegts ☐ Augsts ☑ **Ierobežots (caurspīdīgums)** ☐ Minimāls |
| Piemērojamie pienākumi | 50. p. 1. d. un 2. d.; VDAR (sarunu dati, glabāšanas termiņš, minimizācija, DPIA apsvērt); pieejamība (WCAG: `aria-live="polite"`, tastatūra); Publiskas iestādes informācijas precizitāte |
| Termiņš | **02.08.2026** (caurspīdīguma pienākumi jau piemērojami) |
| Pasākumi dizainā, ja būvētu | Paziņojums "Jūs sarunājaties ar MI palīgu, nevis darbinieku" sākumā un pie katras atbildes; atbildes tikai no apstiprinātas zināšanu bāzes (RAG) ar avota saiti; atteikums atbildēt par individuālām tiesībām/pabalstiem → novirza pie darbinieka; vienmēr redzama saite "Rakstīt darbiniekam" un tālrunis; sarunas netiek glabātas ilgāk par vajadzīgo; regulāra atbilžu pārbaude; iespēja ziņot par kļūdainu atbildi |
| Atlikušie jautājumi juristam | Kas atbild par nepareizu atbildi (iestādes atbildība, labas pārvaldības princips)? Vai vajag DPIA? Vai sarunas drīkst izmantot uzlabošanai? |

## 4. US-15 · "Prioritātes vērtējums" sociālās palīdzības iesniegumiem (NEIMPLEMENTĒT)

| Lauks | Atbilde |
|---|---|
| Komponenta nosaukums | US-15 "Prioritātes vērtējums" |
| Mērķis | Vadītāja lūgums: MI sarindo sociālās palīdzības iesniegumus pēc vajadzības un atzīmē tos, kas "visticamāk neatbilst kritērijiem" |
| Ievade → izvade | Iesniegums (apraksts par personas situāciju: veselība, ienākumi, ģimene) → prioritātes vieta + atzīme "neatbilst" |
| Vai MI sistēma? | **Jā** — vērtēšanas/klasifikācijas modelis vai LLM, kas secina un sniedz vērtējumu |
| Mūsu loma | Nodrošinātājs (ja izstrādājam) + uzturētājs (publiska iestāde) |
| Gala lēmums | Formāli cilvēks, bet sarindojums un "neatbilst" atzīme **faktiski nosaka**, kuru izskata pirmo un kuru, iespējams, nepietiekami rūpīgi (automatizācijas aizspriedums) |
| Ietekme uz personu | **Būtiska**: piekļuve sociālajai palīdzībai, nauda, laiks krīzes situācijā; ievainojamas personas; īpašo kategoriju dati (veselība); diskriminācijas risks |
| Aizliegta prakse (5. p.)? | ☐ Nē ☑ **Jāpārbauda ar juristu**: 5. p. 1. d. c) sociālā vērtēšana — ja vērtējums balstītos uz personas sociālo uzvedību vai personiskām īpašībām un novestu pie nelabvēlīgas attieksmes, kas nav pamatota vai samērīga. Tīrs vajadzību vērtējums pēc likumā noteiktiem kritērijiem visticamāk nav aizliegts, bet robeža ir šaura |
| III pielikuma joma? | ☑ **Jā: 5.a** — publiskas iestādes MI, ko izmanto, lai vērtētu fizisku personu atbilstību būtiskiem publiskās palīdzības pabalstiem un pakalpojumiem |
| 6. p. 3. d. izņēmums? | **Nē.** Nav šaurs procedūras uzdevums, tas aizstāj/ietekmē cilvēka vērtējumu; un tā ir **fizisku personu profilēšana** → saskaņā ar 6. p. 3. d. pēdējo daļu vienmēr augsts risks |
| Caurspīdīgums (50. p.)? | Papildus augsta riska pienākumiem: skartās personas jāinformē (26. p. 11. d.); tiesības uz paskaidrojumu (86. p.) |
| **Riska klase** | ☐ Aizliegts (jāizslēdz pārbaudē) ☑ **Augsts** ☐ Ierobežots ☐ Minimāls |
| Piemērojamie pienākumi | Nodrošinātājam: 8.–17. p. (riska pārvaldība, datu kvalitāte un aizspriedumu pārbaude, tehniskā dokumentācija, žurnāli, caurspīdīgums, cilvēka uzraudzība, precizitāte un noturība, kvalitātes vadība), atbilstības novērtējums, CE, reģistrācija ES datubāzē (49. p.). Uzturētājam (publiskai iestādei): 26. p. (lietošana pēc instrukcijas, kompetenta cilvēka uzraudzība, žurnāli ≥ 6 mēn., skarto personu informēšana), **27. p. pamattiesību ietekmes novērtējums (FRIA)**, 49. p. reģistrācija; 86. p. paskaidrojums. VDAR: DPIA (35. p.), 22. p. automatizēti lēmumi, 9. p. īpašo kategoriju dati |
| Termiņš | **02.12.2027** (III pielikuma augsta riska sistēmas, pēc Omnibusa). Aizliegumi (ja attiektos) — jau no 02.02.2025 |
| Pasākumi / lēmums | **Nebūvēt mācību prototipā.** Pienākumu apjoms (FRIA, atbilstības novērtējums, reģistrācija, datu kvalitāte) nav samērīgs ar ieguvumu, un augsts kaitējuma risks ievainojamām personām. **Alternatīva bez MI:** pārredzami, likumā balstīti kārtošanas noteikumi (iesniegšanas datums, termiņš, likumā noteiktas steidzamības pazīmes, ko atzīmē darbinieks); saraksta filtrs "Sociālā palīdzība" + termiņu kontrole (US-3, US-5); vadītāja pārskats par kavētajiem |
| Atlikušie jautājumi juristam | Vai konkrētie kritēriji nerada 5. p. 1. d. c) risku? Kādi likumā noteikti steidzamības kritēriji pastāv (Sociālo pakalpojumu un sociālās palīdzības likums)? Ja nākotnē būvētu — kurš ir nodrošinātājs, kā organizēt FRIA un DPIA? |

**Atbilde uz grupas jautājumu "vai vērts būvēt mācību prototipā?":** Nē. Mācību prototipā nevar nodrošināt
reprezentatīvus datus, aizspriedumu testēšanu, FRIA un cilvēka uzraudzības procesu, tāpēc tas būtu demonstrējums
tieši tam, kā nedarīt. Vērtīgāk ir parādīt klasifikācijas procesu un pārredzamu alternatīvu bez MI.

## 5. US-7 pasākumu pārbaude pēc īstenošanas

| Pasākums | Kā pārbaudīts | Rezultāts |
|---|---|---|
| Marķējums "Ģenerēts ar MI, pārbaudiet pirms lietošanas" + avots (Claude / imitācija) | `test_ai_block_labelled_and_section` | ✅ |
| Bloks `<section aria-labelledby>`, bez mirgojoša indikatora | `test_ai_block_labelled_and_section`; axe 0 pārkāpumu | ✅ |
| Projekts nonāk atbildes laukā; statuss, atbilde un tēma **nemainās**; nekas netiek nosūtīts | `test_use_projekts_fills_field_but_never_sends` | ✅ |
| Tēma mainās tikai ar atsevišķu pogu un tiek žurnalēta | `test_mi_topic_change_is_explicit_and_logged` | ✅ |
| `notikumi`: "MI ieteikums (imitacija) izmantots…", "Tēma mainīta pēc MI ieteikuma…" | testi; redzams detaļu vēsturē | ✅ |
| Līgums `{tema, atbildes_projekts}`; imitācija bez tīkla; Claude kļūdas gadījumā → imitācija | `test_contract_and_imitation_without_network`, `test_claude_failure_falls_back` | ✅ |
| Slēgtiem iesniegumiem MI bloka nav | `test_no_ai_block_on_closed` | ✅ |
| Apraksts netiek rakstīts žurnālā (`logging`) | koda pārskats `ai.py` (žurnālā tikai kļūdas veids) | ✅ |
| Claude API ar īstu atslēgu | — | ⬜ nav pārbaudīts (atslēgas nav) |

### 5 "grūti" testa iesniegumi (veidnes 6. sadaļa), imitācija

| Gadījums | Teksts | Pareizā tēma | Imitācija | Vērtējums |
|---|---|---|---|---|
| Divdomīgs | «Pie bērnudārza ir tumšs, jo nedeg lampa.» | Ielu apgaismojums | Ielu apgaismojums | ✅ |
| Vairākas problēmas | «Bedre ceļā un blakus pārpildīts atkritumu konteiners, kas netiek izvests.» | Abas (Ceļi / Atkritumi) | Atkritumi | 🟡 viena problēma pazūd |
| Sarkasms | «Paldies, ka mūsu ielā tagad ir 'ezers' — bedre tik liela, ka var makšķerēt.» | Ceļi un bedres | Ceļi un bedres | ✅ (atslēgvārds "bedre"); atbildes tonis neņem vērā sarkasmu |
| Bez atslēgvārdiem | «Kaimiņš katru nakti skaļi klausās mūziku.» | Cits | Cits | ✅ |
| Sociālā + bērnudārzs | «Zaudēju darbu, nevaru samaksāt par bērnudārzu, vai ir kāds pabalsts?» | **Sociālā palīdzība** | **Bērnudārza rinda** | ❌ **kļūda** |

**Secinājums no testiem:** pēdējā kļūda ir tieši tā, no kuras brīdina veidne: ja tēma "Sociālā palīdzība" tiktu nepareizi nomainīta,
cilvēks krīzes situācijā varētu nonākt nepareizā rindā. Tāpēc dizainā **tēma nekad netiek mainīta automātiski**, un ieteikums
to tikai piedāvā ar atsevišķu pogu. Klasifikācija paliek **minimāls risks**, bet ieteikums: sociālās palīdzības tēmai
MI ieteikumu rādīt ar papildu brīdinājumu vai neizmantot (jautājums juristam, 2. nodaļa). Testi: `tests/test_iesn_mi.py::HARD_CASES`.
