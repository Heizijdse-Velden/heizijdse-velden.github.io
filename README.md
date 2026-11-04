# Ondergrondse containers Turnhout: meertalige uitleg

Een kleine statische website met een vertaalde uitleg van de IOK-handleiding voor de ondergrondse afvalcontainers, in 10 talen. Er hoort een A4-affiche met QR-code bij. Alles wordt gebouwd uit tekstbestanden en staat gratis op GitHub Pages.

- **Site:** taalkiezer (`/`), één pagina per taal (`/nl/`, `/en/`, `/ar/`, …) en de affiche (`/affiche/`)
- **Talen:** Nederlands, English, Français, العربية, Türkçe, Polski, Română, Български, Українська, Español
- **Geen** cookies, tracking, formulieren, externe scripts of lettertypes. Een Content-Security-Policy blokkeert alles wat niet van de site zelf komt.

---

## 1. Online zetten (eenmalig, ±15 minuten)

1. **GitHub-account** voor elke beheerder, met **tweestapsverificatie (2FA)** aan.
2. Maak een gratis **organisatie** `afval-turnhout`, of een andere naam (zie stap 6). Voeg minstens **2 beheerders als Owner** toe. Zo hangt de site niet aan één persoon.
3. Maak in die organisatie een **publieke repository** met de naam `afval-turnhout.github.io`. Die naam geeft het korte adres `https://afval-turnhout.github.io/`.
4. Zet deze bestanden erin:
   ```bash
   git init -b main && git add . && git commit -m "Eerste versie"
   git remote add origin https://github.com/afval-turnhout/afval-turnhout.github.io.git
   git push -u origin main
   ```
5. Ga naar **Settings → Pages → Build and deployment → Source: GitHub Actions**. Na ±1 minuut staat de site online. De voortgang zie je onder **Actions**.
6. Andere naam gekozen? Pas dan `site_url` in `site.json` aan. De QR-code en de affiche worden daaruit gemaakt.

> Bij een gewone repository (bv. `buurt/afval`) wordt het adres `https://buurt.github.io/afval/`. Dat werkt ook, maar het is langer om over te typen.

## 2. Affiche printen

1. Vul `publisher` in `site.json` in. Wettelijk moet op elk gedrukt werk een **verantwoordelijke uitgever (V.U.)** staan: de naam en het adres van een meerderjarige inwoner van België. Zolang dat veld leeg is, staat er een rode waarschuwing op de affiche.
2. Open `https://<jouw-site>/affiche/` in Chrome en kies **Afdrukken → Opslaan als PDF**: A4, marges *Geen*, *Achtergrondafbeeldingen* aan. Je kan ook `python tools/affiche_pdf.py` gebruiken.
3. **Scan de QR-code zelf** voor je print, en controleer of je op het juiste adres uitkomt.
4. Laat de affiche plastificeren, of print op weerbestendig papier of folie.

## 3. Teksten aanpassen

Alle teksten staan in `content/<taal>.json`. De affiche gebruikt `content/poster.json`. Contactgegevens en links staan in `site.json` en worden op één plek beheerd.

- **Via de website van GitHub:** open het bestand, klik op het potloodje, pas aan en klik op *Commit changes*. Binnen ±1 minuut staat de nieuwe versie online.
- Elke taal moet **exact dezelfde sleutels** hebben als `nl.json`. Ontbreekt er iets, of is iets leeg, dan stopt de bouw met een duidelijke foutmelding. De **vorige versie blijft dan online**, er gaat dus niets kapot.
- Tekst wordt altijd als gewone tekst getoond (HTML wordt ge-escaped). Een vertaler kan dus per ongeluk geen code toevoegen.
- Nederlandse woorden die letterlijk blijven staan, zoals de schermtekst *welkom, bied je pas aan*, staan in `dutch_terms` in `site.json`. Ze worden dan ook in het Arabisch (rechts-naar-links) correct weergegeven.

Lokaal bouwen en bekijken:
```bash
python -m venv .venv && . .venv/bin/activate
pip install --require-hashes --no-deps -r requirements.txt
python build.py && python -m http.server -d _site 8000   # open http://localhost:8000
python build.py --check                                   # enkel controleren
```

### Een taal toevoegen

1. Kopieer `content/en.json` naar `content/<code>.json` (ISO-code, bv. `ps`, `so`, `ti`) en vertaal de teksten.
2. Zet `"dir": "rtl"` voor talen die van rechts naar links lopen (Arabisch, Pasjtoe, Dari, Perzisch, Hebreeuws).
3. Voeg de code toe aan `languages` en `sorting_guides` in `site.json`. Bestaat er geen IOK-sorteergids in die taal, gebruik dan die in het Engels.

### Vertalingen laten nalezen

De vertalingen zijn een eerste versie, gemaakt met AI. **Laat elke taal nalezen door iemand uit de buurt die ze als moedertaal spreekt.** Let daarbij vooral op:
- dat de tekst eenvoudig is (taalniveau A2–B1), met korte zinnen;
- de woorden voor *toegangspas*, *restafval*, *PMD* en *recyclagepark*;
- dat de Nederlandse schermteksten tussen aanhalingstekens blijven staan.

## 4. Onderhoud (2× per jaar, ±15 minuten)

- [ ] Vergelijk met [iok.be/ondergrondse-containers](https://www.iok.be/ondergrondse-containers) en de handleiding (PDF): zijn er nieuwe telefoonnummers, uren, zakgroottes of de prijs van een nieuwe pas?
- [ ] Klik alle links op de site even aan.
- [ ] Zet `last_reviewed` in `site.json` op de datum van vandaag.
- [ ] Controleer de affiches ter plaatse: is er **geen sticker over de QR-code geplakt**? Scan ze.
- [ ] Werk de versies van de GitHub Actions en `requirements.txt` bij als GitHub waarschuwt. Hashes genereer je met `pip-compile --generate-hashes`.

## 5. Veiligheid

Het grootste risico zit niet in de website, maar in een **valse QR-sticker** die iemand over de echte plakt ("quishing"), bijvoorbeeld met een link als "betaal €5 voor je nieuwe pas". Dit beschermt ertegen:
- Het adres staat **leesbaar onder de QR-code**, en de site zegt in elke taal dat ze **nooit om geld of gegevens vraagt**.
- **Geen URL-verkorters** en **geen "dynamische QR-codes"** van gratis generators: die kunnen verdwijnen, betalend worden of gekaapt worden. De QR-code hier wijst rechtstreeks naar de site en wordt lokaal gemaakt.
- Het gratis `github.io`-adres **verloopt nooit**. Kies je toch een eigen domein, betaal het dan voor meerdere jaren vooruit en zet automatische verlenging aan. Een verlopen domein kan iemand anders opkopen, en dan wijzen al je affiches naar zijn site.
- Laat minstens 2 beheerders met 2FA toe. Zet eventueel *branch protection* op `main` (Settings → Branches), zodat wijzigingen eerst nagekeken worden.
- Voeg geen analytics, formulieren, ingesloten video's of scripts van derden toe. De Content-Security-Policy blokkeert ze ook.

## 6. Juridisch (geen juridisch advies)

- **Toelating voor de affiche:** de containers zijn van IOK. Het politiereglement van Turnhout vereist een schriftelijke vergunning voor opschriften op straatmeubilair. Vraag daarom eerst toelating; een mailtje staat in [`docs/mail-aan-iok.md`](docs/mail-aan-iok.md). Hou het scherm, de pasjeslezer en de inwerpopening altijd vrij. Alternatieven zonder openbaar domein: inkomhallen (met akkoord van de syndicus of woonmaatschappij), het buurthuis of flyers in de bus.
- **Verantwoordelijke uitgever** op elk drukwerk (zie hierboven).
- **Taalwetgeving:** die geldt voor overheden (stad, IOK), niet voor privévrijwilligers. De vertalingen zijn bewust opgesteld als "vertaling van de Nederlandstalige IOK-tekst". Zo kunnen de stad of IOK ze later ook gebruiken.
- **Auteursrecht:** de site gebruikt geen foto's of logo van IOK, alleen eigen pictogrammen en links naar hun materiaal. Wil je foto's? Neem dan zelf foto's van jullie containers. Dat is ook herkenbaarder voor de bewoners.

## Bestanden

```
site.json              instellingen: URL, talen, contactgegevens, links, V.U.
content/<taal>.json    teksten per taal
content/poster.json    teksten van de affiche
templates/             HTML-sjablonen (Jinja2) + pictogrammen (_icons.html)
static/                CSS, kleine taalsuggestie (lang.js), favicon
build.py               controleert en bouwt naar _site/ (incl. qr.svg en qr.png)
tools/affiche_pdf.py   optioneel: affiche als PDF
.github/workflows/     automatisch bouwen en publiceren
docs/mail-aan-iok.md   voorbeeldmail om toelating te vragen
```
