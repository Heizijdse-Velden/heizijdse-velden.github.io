# Heizijdse Velden: uitleg ondergrondse containers

Meertalige uitleg (10 talen) over de ondergrondse afvalcontainers in Turnhout, met een A4-affiche en QR-code.
Live op **https://heizijdse-velden.github.io/**

## Lokaal

Vereist: [uv](https://docs.astral.sh/uv/).

```bash
uv run sitegen serve    # bouwen + bekijken op http://localhost:8000
uv run sitegen check    # enkel de teksten controleren
uv run pytest           # tests
```

## Affiche (PDF)

```bash
uv run --group poster playwright install chromium   # eenmalig
uv run --group poster sitegen poster                # → affiche.pdf
```

Scan de QR-code voor je print. De verantwoordelijke uitgever (V.U.: naam + adres) staat in `content/site.json`.

## Teksten aanpassen

| Wat | Waar |
|---|---|
| Teksten per taal | `content/lang/<taal>.json` |
| Affiche | `content/poster.json` |
| URL, contactgegevens, links, V.U. | `content/site.json` |

Elke taal moet dezelfde sleutels hebben als `nl.json`. Zo niet, dan faalt de build en blijft de vorige versie online.
Een taal toevoegen: kopieer `en.json`, vertaal, en voeg de code toe aan `languages` en `sorting_guides` in `site.json` (`"dir": "rtl"` voor Arabisch e.d.).

## Publiceren

Push naar `main`: GitHub Actions lint, test, bouwt en publiceert.
Eenmalig instellen: **Settings → Pages → Source: GitHub Actions**.

Onderhoud, veiligheid en juridische aandachtspunten: [`docs/beheer.md`](docs/beheer.md).
