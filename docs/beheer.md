# Beheer

## Onderhoud (2× per jaar)

- Vergelijk met [iok.be/ondergrondse-containers](https://www.iok.be/ondergrondse-containers) en de IOK-handleiding: zijn telefoonnummers, uren, zakgrootte of de prijs van een nieuwe pas veranderd?
- Klik de links op de site aan.
- Zet `last_reviewed` in `content/site.json` op de datum van vandaag.
- Controleer de affiches ter plaatse: is er geen sticker over de QR-code geplakt? Scan ze.
- Afhankelijkheden bijwerken: `uv lock --upgrade && uv run pytest`.

## Vertalingen

De vertalingen zijn een eerste versie, gemaakt met AI. Laat elke taal nalezen door iemand die ze als moedertaal spreekt. Let daarbij op:

- eenvoudige taal (A2–B1);
- de termen *toegangspas*, *restafval*, *PMD* en *recyclagepark*;
- de Nederlandse schermteksten tussen aanhalingstekens moeten letterlijk blijven staan.

Nederlandse woorden die in vertalingen voorkomen, staan in `dutch_terms` in `content/site.json`. Ze worden dan correct weergegeven in talen die van rechts naar links lopen.

## Veiligheid

- Het grootste risico is een **valse QR-sticker** over de echte ("quishing"). Daarom staat de URL leesbaar onder de QR-code, en zegt de site in elke taal dat ze nooit om geld of gegevens vraagt.
- Gebruik geen URL-verkorters of "dynamische QR-codes". De QR-code wordt hier lokaal gemaakt en wijst rechtstreeks naar de site.
- Het `github.io`-adres verloopt nooit. Kies je toch een eigen domein: betaal het meerdere jaren vooruit en zet automatische verlenging aan.
- Zorg voor minstens 2 beheerders van de GitHub-organisatie, met 2FA. Zet eventueel branch protection op `main`.
- Geen analytics, formulieren of scripts van derden: de Content-Security-Policy blokkeert ze, en een test bewaakt dat.

## Juridisch (geen juridisch advies)

- **Affiche aan de containers:** die zijn van IOK, en het politiereglement van Turnhout vereist een vergunning voor opschriften op straatmeubilair. Vraag eerst toelating (zie [`mail-aan-iok.md`](mail-aan-iok.md)). Houd het scherm, de pasjeslezer en de inwerpopening vrij.
- **V.U.:** de naam en het adres van een meerderjarige inwoner van België moeten op elk drukwerk staan.
- **Taalwetgeving** geldt voor overheden, niet voor privévrijwilligers. De vertalingen zijn opgesteld als vertaling van de Nederlandstalige IOK-tekst.
- **Auteursrecht:** de site gebruikt geen foto's of logo van IOK, alleen eigen pictogrammen en links.
