# Heizijdse Velden: uitleg ondergrondse containers

Meertalige uitleg (10 talen) over de ondergrondse afvalcontainers in Turnhout, met een A4-affiche en QR-code.
Live op **https://heizijdse-velden.github.io/**

## Lokaal

Vereist: [uv](https://docs.astral.sh/uv/).

```bash
uv run playwright install chromium   # eenmalig: voor browsertests en de affiche
uv run sitegen serve                 # bouwen + bekijken op http://localhost:8000
uv run pytest                        # alle tests (inhoud, HTML, browser)
uv run pytest -m external            # werken de externe links nog? (draait ook wekelijks in CI)
uv run sitegen poster                # affiche → affiche.pdf
```

Scan de QR-code voor je print. De verantwoordelijke uitgever (V.U.: naam + adres) staat in `content/site.json`.

## Teksten aanpassen

| Wat | Waar |
|---|---|
| Teksten per taal | `content/lang/<taal>.json` |
| Affiche | `content/poster.json` |
| URL, contactgegevens, links, V.U. | `content/site.json` |

Elke taal moet dezelfde sleutels hebben als `nl.json`. Zo niet, dan faalt de build en blijft de vorige versie online.
Een taal toevoegen: kopieer `en.json`, vertaal, en voeg de code toe aan `languages`, `sorting_guides` en `fostplus_sites` in `site.json` (`"dir": "rtl"` voor Arabisch e.d.).

## Publiceren

Open een PR: GitHub Actions lint, auditeert de workflows (zizmor), test en bouwt. Na de merge naar `main` wordt de site gepubliceerd.

Onderhoud, veiligheid en juridische aandachtspunten: [`docs/beheer.md`](docs/beheer.md).
