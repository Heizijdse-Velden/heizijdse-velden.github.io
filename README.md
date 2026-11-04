# Heizijdse Velden: uitleg ondergrondse containers

Meertalige uitleg (10 talen) over de ondergrondse afvalcontainers in Turnhout, met een A4-affiche en QR-code.
Live op **https://heizijdse-velden.github.io/**

## Snel starten

Vereist: [uv](https://docs.astral.sh/uv/).

```bash
uv run playwright install chromium   # eenmalig: voor de browsertests en de affiche
uv run sitegen serve                 # bouwen en bekijken op http://localhost:8000
```

| Commando | Wat het doet |
|---|---|
| `uv run sitegen check` | Teksten controleren: elke taal volledig, alle links geldig |
| `uv run sitegen poster` | Affiche maken: `outputs/affiche.pdf` |
| `uv run pytest --cov` | Alle tests, met dekkingsrapport (minimum 95%) |
| `uv run pytest -m external` | Werken de externe links nog? |
| `uv run ruff check && uv run mypy` | Codestijl (PEP 8/257) en types |

Scan de QR-code voor je de affiche print. De verantwoordelijke uitgever (V.U.: naam + adres) staat in `content/site.json`.

## Teksten aanpassen

| Wat | Waar |
|---|---|
| Teksten per taal | `content/lang/<taal>.json` |
| Affiche | `content/poster.json` |
| URL, contactgegevens, links, V.U. | `content/site.json` |

Elke taal moet dezelfde sleutels hebben als `nl.json`. Ontbreekt er iets, dan faalt de build met een duidelijke melding en blijft de vorige versie online.

Een taal toevoegen: kopieer `en.json` naar `<code>.json`, vertaal het, en voeg de code toe aan `languages`, `sorting_guides` en `fostplus_sites` in `site.json`. Voor Arabisch en andere talen die van rechts naar links lopen zet je `"dir": "rtl"`.

## Hoe het werkt

```
content/        teksten en instellingen (JSON)  ─┐
src/sitegen/    Python: controleren en bouwen    ├─► _site/  ─► GitHub Pages
  templates/    HTML (Jinja2) en pictogrammen    │
  static/       CSS en één klein script          ─┘
tests/          inhoud, HTML, CLI, browser (Playwright), externe links
```

## Publiceren

Open een PR. GitHub Actions voert dezelfde controles uit als hierboven en bouwt de site. Na de merge naar `main` staat de nieuwe versie binnen een minuut online.

Onderhoud, veiligheid en juridische aandachtspunten: [`docs/beheer.md`](docs/beheer.md).
