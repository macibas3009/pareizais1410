# Iesniegumi · Ezermalas novada pašvaldība (mācību prototips)

Iedzīvotāju iesniegumu sistēma: bedres, apgaismojums, atkritumi, bērnudārza rinda, sociālā palīdzība.
Trīs lomas (iedzīvotājs, darbinieks, vadītājs), 8 ekrāni, MI ieteikums darbiniekam. Visi dati ir sintētiski.

## Palaišana

```bash
cd iesniegumi
pip install -r requirements.txt   # Flask
make init                         # izveido data.db no schema.sql + 10 testa iesniegumi
make run                          # http://localhost:8001  (vai: python app.py)
```

Sākumlapā izvēlas lomu (bez paroles, mācību režīms).

## Pārbaudes

```bash
make test     # pytest: pieņemšanas kritēriji
make a11y     # axe-core + Playwright: WCAG 2.2 AA, tastatūra, 320 px, 200 % → a11y-report.md
```

`make a11y` vajag `pip install playwright axe-playwright-python && python -m playwright install chromium`.

## Dokumentācija

| Dokuments | Saturs |
|---|---|
| [docs/BACKLOG.md](docs/BACKLOG.md) | Kursa backlogs (avots) |
| [docs/prasibas.md](docs/prasibas.md) | Prasības ar pieņemšanas kritērijiem un statusu |
| [docs/process.md](docs/process.md) | Izstrādes process un Definition of Done |
| [docs/mi-riska-novertejums.md](docs/mi-riska-novertejums.md) | MI riska novērtējums: US-7, US-10, US-15 |
| [docs/pieejamibas-atskaite.md](docs/pieejamibas-atskaite.md) | Pieejamības atskaite un testēšanas protokols |
| [a11y-report.md](a11y-report.md) | Automātiskā testa rezultāts |
| [docs/prezentacija.pptx](docs/prezentacija.pptx) | Prezentācija: secība, process, secinājumi |

## Definition of Done

Sk. [docs/process.md](docs/process.md#2-definition-of-done-katram-us).
