# Beheer

## Wat automatisch gebeurt

| Wanneer | Wat |
|---|---|
| Elke PR en push | Codestijl (ruff), types (mypy), audit van de workflows (zizmor), tests met minstens 95% dekking, build |
| Merge naar `main` | Publicatie op GitHub Pages, alleen als alles groen is |
| Elke maandag | Check van alle externe links (IOK, Fost Plus, YouTube). Bij een fout krijg je een mail van GitHub. |
| Elke maand | Dependabot-PR's voor GitHub Actions en Python-pakketten (minstens 7 dagen oud) |

## Onderhoud (2× per jaar, ±15 minuten)

- Vergelijk met [iok.be/ondergrondse-containers](https://www.iok.be/ondergrondse-containers) en de IOK-handleiding: zijn telefoonnummers, uren, zakgrootte of de prijs van een nieuwe pas veranderd?
- Zet `last_reviewed` in `content/site.json` op de datum van vandaag.
- Controleer de affiches ter plaatse: is er geen sticker over de QR-code geplakt? Scan ze.

## Affiches drukken

1. `uv run sitegen poster` maakt `outputs/affiche.pdf`. Scan de QR-code voor je print.
2. Zet een tag op de versie die je drukt, bv. `git tag affiche-2026-11 && git push --tags`. Zo weet je later altijd welke tekst (URL, telefoonnummer, V.U.) er op straat hangt.

Releases zijn verder niet nodig: elke merge naar `main` is meteen de live versie, en de commitgeschiedenis is het logboek.

## Vertalingen

De vertalingen zijn een eerste versie, gemaakt met AI. Laat elke taal nalezen door iemand die ze als moedertaal spreekt. Let daarbij op:

- eenvoudige taal (A2–B1);
- de termen *toegangspas*, *restafval*, *PMD* en *recyclagepark*;
- de Nederlandse schermteksten (“Welkom, bied je pas aan.”) moeten letterlijk blijven staan.
- Frans: vóór `? ! : ;` hoort een vaste spatie (no-break space), geen gewone spatie. Een test controleert dat.

Pas je een Nederlandse tekst aan? Pas dan ook dezelfde sleutel aan in de andere talen. De tests controleren dat elke sleutel bestaat, maar niet of de inhoud nog klopt.

## Veiligheid

Al automatisch geregeld:

- **Website:** geen cookies, tracking, formulieren of scripts van derden. Een Content-Security-Policy blokkeert alles wat niet van de site zelf komt, en tests bewaken dat. Vertaalde tekst wordt altijd ge-escaped, zodat er geen HTML in kan sluipen.
- **Pipeline:**
  - Actions staan vast op een commit-SHA.
  - Workflows hebben minimale rechten en `persist-credentials: false`.
  - zizmor auditeert de workflows bij elke PR.
  - Dependabot houdt de vaste versies bij, met 7 dagen cooldown.
- **Affiche:** de site vraagt nooit om geld of gegevens, en dat staat al op de affiche zelf. Een valse QR-sticker die naar een betaalpagina leidt, valt zo meteen op.

Eenmalig zelf aanzetten in de GitHub-instellingen (kan niet vanuit de repo):

- [ ] **Settings → Advanced Security:** Dependabot alerts, secret scanning + push protection, private vulnerability reporting
- [ ] **Settings → Actions → General:** "Require actions to be pinned to a full-length commit SHA"; workflow permissions op *Read repository contents*; "Allow GitHub Actions to create and approve pull requests" uit
- [ ] **Settings → Branches (`main`):** required status check `build`; force pushes en verwijderen blokkeren
- [ ] **Organisatie → Authentication security:** 2FA verplicht. Zorg ook voor minstens 2 owners.

## Juridisch (geen juridisch advies)

- **Affiche aan de containers:** die zijn van IOK, en het politiereglement van Turnhout vereist een vergunning voor opschriften op straatmeubilair. Vraag eerst toelating (zie [`mail-aan-iok.md`](mail-aan-iok.md)) en houd het scherm, de pasjeslezer en de inwerpopening vrij.
- **V.U.:** naam en adres van een meerderjarige inwoner van België, op elk drukwerk.
- **Taalwetgeving** geldt voor overheden, niet voor privévrijwilligers. De vertalingen zijn opgesteld als vertaling van de Nederlandstalige IOK-tekst.
- **Auteursrecht:** de site gebruikt geen foto's of logo van IOK, alleen eigen pictogrammen en links.
