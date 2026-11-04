#!/usr/bin/env python3
"""Optioneel: maakt affiche.pdf van _site/affiche/ zonder browser-printdialoog.

Eenmalig:  pip install playwright && playwright install chromium
Gebruik:   python build.py && python tools/affiche_pdf.py

Zonder dit script kan het ook: open https://<jouw-site>/affiche/ in Chrome,
kies Afdrukken → Opslaan als PDF → A4, marges 'Geen', 'Achtergrondafbeeldingen' aan.
"""
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
src = ROOT / "_site" / "affiche" / "index.html"
out = ROOT / "affiche.pdf"

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto(src.as_uri())
    page.emulate_media(media="print")
    page.pdf(path=str(out), format="A4", print_background=True,
             margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
             prefer_css_page_size=True)
    browser.close()
print(f"Klaar: {out}")
