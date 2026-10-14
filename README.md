# M1 · Vides pārbaude un API līgums

Šī repozitorija ir FITA 1. moduļa obligātajam vides pārbaudes uzdevumam **A0** un izvēles uzdevumam **A1**. Visi piemēra dati ir sintētiski; Ezermalas novada pašvaldība un OMD reģistrs ir izdomāti.

## A0 · Vides pārbaude

1. Izveido vai apstiprini savu personīgo GitHub kontu.
2. Izveido savu repozitoriju no šīs veidnes.
3. Atver repozitoriju GitHub Codespaces un sagaidi, līdz vide ir gatava.
4. Terminālī palaid `claude` un piesakies ar kursa Claude kontu.
5. Uzdod Claude jautājumu: `Explain what make test does`.
6. Saglabā Claude atbildi failā `setup/claude-answer.md`.
7. Palaid `make verify-setup`.
8. Izveido zaru `setup-ok`, veic komitu un nosūti zaru uz GitHub.
9. GitHub cilnē **Actions** pārliecinies, ka pārbaude ir zaļa.

Fails `setup/claude-answer.md` apstiprina, ka Claude Code pieteikšanās Codespace vidē ir izdevusies. Tukšs vai neesošs fails neizturēs pārbaudi.

Pašas veidnes CI izveido īslaicīgu atbildes failu tikai `mleitass/m1-setup-check`
izpildes vidē. No veidnes izveidotajās dalībnieku repozitorijās šis solis netiek
izpildīts, tāpēc dalībnieka atbildes fails joprojām ir obligāts.

## A1 · Līgums pirms koda (izvēles uzdevums)

Izlasi `tracker/CR-2.md` un papildini CR-2 daļu failā `docs/openapi.yaml`:

- dokumentē 5xx un noildzes uzvedību;
- pievieno pilnu `reasonCode` vērtību sarakstu;
- pievieno `PENDING_CHANNEL_CHECK` atbildes kanālu;
- nodrošini, ka katrai operācijai ir `400`, `404` un vismaz viena `5xx` atbilde;
- visām kļūdu atbildēm izmanto kopīgo `Error` shēmu ar `$ref`.

Pārbaudi rezultātu ar:

```bash
make lint-contract
```

Sākotnējā līguma versija šo pārbaudi neiztur apzināti. Uzdevums ir pabeigts, kad komanda beidzas veiksmīgi.

## Komandas

| Komanda | Nozīme |
|---|---|
| `make verify-setup` | Pārbauda Python, kursa pakotnes, Claude Code, saglabāto atbildi un smoke testus |
| `make test` | Palaiž visus `pytest` testus |
| `make lint-contract` | Validē OpenAPI dokumentu un kursa līguma noteikumus |

## CRM prototips (Ezermalas novada pašvaldība)

Šajā repozitorijā ir arī mācību CRM mazai iestādei: Flask + Jinja2 + SQLite, servera pusē renderēts HTML,
kas strādā bez JavaScript. Visi dati ir sintētiski.

```bash
make install      # Flask (requirements.txt)
make seed         # sintētiski sākumdati: 4 lietotāji, 10 organizācijas, 20 kontakti, 30 mijiedarbības
make run          # http://localhost:8000/login
```

Testa lietotāji (parole `app/seed.py` vai vides mainīgajā `SEED_PASSWORD`): `darbinieks@example.com`,
`darbinieks2@example.com`, `vaditajs@example.com`, `admin@example.com`.

| Komanda | Nozīme |
|---|---|
| `make test` | Visi `pytest` testi, arī CRM pieņemšanas kritēriji |
| `make install-dev` | Playwright, Chromium un axe pārbaudēm (`requirements-dev.txt`) |
| `make a11y` | Piekļūstamības pārbaude (axe-core, 320 px, 200 %, tastatūra) → `docs/a11y-rezultati.json` → lapa `/pieklustamiba` |
| `make ekranu-karte` | Atjauno `docs/ekranu-karte.png` no `docs/ekranu-karte.html` |
| `make users`, `make role EMAIL=… ROLE=…` | Lomu pārvaldība no termināļa (rezerves variants; ikdienā to dara administrators lapā `/lietotaji`) |

MI-1 kopsavilkums strādā bez ārēja pakalpojuma (atslēgvārdu imitācija). Lai izmantotu Claude API:
`pip install anthropic` un vides mainīgais `ANTHROPIC_API_KEY` (modelis: `MI_MODEL`, noklusēti `claude-opus-5-5`).

Dokumentācija: [prasību saraksts](docs/prasibu-saraksts.md) (ar izpildes statusu) ·
[ekrānu karte](docs/ekranu-karte.md) · [vadības panelis](docs/vadibas-panelis.md) ·
[MI-2 klasifikācija](docs/mi2-klasifikacija.md) · [realizācijas plāns](docs/realizacijas-plans.md)
