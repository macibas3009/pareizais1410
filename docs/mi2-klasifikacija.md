# MI-2 · Organizāciju prioritizācija "pēc sadarbības potenciāla": klasifikācija

> 2026-10-14 · Mācību projekts. Šī ir prasību analīze, nevis juridisks atzinums: pirms jebkādas izstrādes
> klasifikācija jāpārbauda iestādes juristam un datu aizsardzības speciālistam.
> Saistīts: [prasību saraksts](prasibu-saraksts.md), MI-2.

## Lēmums

**Nebūvēt.** Funkcija netiek īstenota šajā projektā. Tās vietā vadītājs izmanto pārredzamu pārskatu (F7),
kurā ir faktiski skaitļi (mijiedarbības, kavētie pieprasījumi), nevis MI piešķirts vērtējums.

## 1. Ko funkcija darītu

MI sistēma katrai organizācijai piešķirtu "sadarbības potenciāla" vērtējumu vai secību, piemēram,
"augsts / vidējs / zems". Darbinieki pēc tā izvēlētos, kurām organizācijām veltīt laiku: konsultācijas,
semināri, atbildes uz pieprasījumiem.

## 2. Kas tiktu vērtēts

| Kas | Kāpēc tas ir svarīgi |
|---|---|
| **Organizācijas**: uzņēmumi, NVO, pašvaldības | Tiešais vērtējuma objekts |
| **Fiziskas personas netieši** | Mazās NVO un individuālie komersanti faktiski ir konkrēti cilvēki. Kontaktpersonu dati (mijiedarbības, amati) būtu modeļa ievaddati |
| **Ievaddati** | Mijiedarbību biežums un saturs, pieprasījumi, nozare, iespējams, brīvais teksts no kopsavilkumiem |
| **Vēsturiskie dati** | Modelis mācītos no pagātnes izvēlēm. Tas var nostiprināt esošos aizspriedumus, piemēram, par labu lielām organizācijām, kas jau tagad saņem vairāk uzmanības |

## 3. Sekas organizācijai un personai

- **Mazāka piekļuve publiskam pakalpojumam.** Organizācija ar zemu vērtējumu saņemtu mazāk konsultāciju un vēlākas atbildes. Tā ir publiskas iestādes pakalpojuma sadale, nevis komercdarbība.
- **Necaurredzamība.** Organizācija nezinātu, ka to vērtē, un nevarētu vērtējumu apstrīdēt.
- **Pašpiepildošs pareģojums.** Mazāk uzmanības nozīmē mazāk mijiedarbību, tas nozīmē vēl zemāku vērtējumu.
- **Diskriminācijas risks.** Netiešas pazīmes (reģions, valoda, organizācijas lielums) var korelēt ar aizsargātām grupām.

## 4. Riska klase pēc MI akta (Regula (ES) 2024/1689)

| Jautājums | Vērtējums |
|---|---|
| Aizliegta prakse (5. pants, sociālā novērtēšana) | **Jāizslēdz pārbaudē.** Ja vērtējums attiektos uz fiziskām personām un vestu pie nelabvēlīgas attieksmes, tas varētu tuvoties aizliegtai sociālajai novērtēšanai |
| Augsta riska joma (6. pants, III pielikums) | **Iespējams augsts risks.** III pielikuma 5. punkts: publiskas iestādes MI, kas izvērtē piekļuvi būtiskiem publiskiem pakalpojumiem. Ja tiek veikta fizisku personu profilēšana, sistēma vienmēr ir augsta riska (6. panta 3. punkts) |
| Izņēmums "tikai sagatavošanas uzdevums" (6. panta 3. punkts) | **Nav piemērojams droši.** Vērtējums tieši ietekmētu lēmumu par uzmanības sadali, un ievaddatos ir kontaktpersonu dati |
| Ja būtu augsts risks, pienākumi iestādei kā ieviesējai | Cilvēka pārraudzība, žurnāli, darbinieku apmācība (26. pants); pamattiesību ietekmes novērtējums publiskām iestādēm (27. pants); informēšana |
| VDAR | Profilēšana: datu aizsardzības ietekmes novērtējums (35. pants), pārredzamība, tiesības iebilst |

**Secinājums:** iespējams **augsta riska** sistēma. Pat ja juridiskā pārbaude to klasificētu zemāk, ieguvums
(ērtāka darba plānošana) neattaisno pārredzamības un taisnīguma riskus, ja ir vienkārša alternatīva bez MI.

## 5. Salīdzinājums ar MI-1

| | MI-1 (kopsavilkums) | MI-2 (prioritizācija) |
|---|---|---|
| Ko dara | Pārraksta darbinieka piezīmes | Vērtē organizācijas |
| Lēmums par cilvēku vai organizāciju | Nē | Jā, netieši |
| Cilvēka kontrole | Katrs rezultāts tiek apstiprināts pirms saglabāšanas | Vērtējums ietekmētu darbu bez katras izvēles pārbaudes |
| Riska klase | Minimāls risks; marķējums "Ģenerēts ar MI" | Iespējams augsts risks |
| Lēmums | Būvēts | **Nebūvēt** |

## 6. Nosacījumi, ar kādiem lēmumu var pārskatīt

1. Juridisks MI akta klasifikācijas atzinums un datu aizsardzības ietekmes novērtējums (DPIA).
2. Ievaddatos nav fizisku personu datu (tikai organizāciju līmeņa agregāti).
3. Vērtēšanas kritēriji ir publiski un saprotami. Organizācija var uzzināt savu vērtējumu un to apstrīdēt.
4. Rezultāts ir tikai ieteikums. Katru prioritātes maiņu apstiprina un pamato cilvēks, un tas tiek žurnalēts.
5. Regulāra novirzes (bias) pārbaude pēc organizāciju lieluma, reģiona un veida.
6. Pierādīts, ka pārredzami noteikumi bez MI (piem., F7 pārskats un termiņi) nav pietiekami.
