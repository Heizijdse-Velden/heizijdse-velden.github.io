"""Print the poster page to an A4 PDF with headless Chromium (Playwright)."""

from __future__ import annotations

from pathlib import Path

from playwright.sync_api import Browser, sync_playwright
from playwright.sync_api import Error as PlaywrightError

INSTALL_HINT = "The poster needs Chromium. Install it once with:\n  uv run playwright install chromium"


def print_pdf(browser: Browser, html_path: Path, pdf_path: Path) -> None:
    """Print ``html_path`` to ``pdf_path`` as A4 without margins, backgrounds included."""
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    page = browser.new_page()
    try:
        page.goto(html_path.resolve().as_uri())
        page.emulate_media(media="print")
        page.pdf(path=str(pdf_path), print_background=True, prefer_css_page_size=True)
    finally:
        page.close()


def render_pdf(html_path: Path, pdf_path: Path) -> None:
    """Start Chromium and print the poster. Exit with install instructions if Chromium is missing."""
    with sync_playwright() as playwright:
        try:
            browser = playwright.chromium.launch()
        except PlaywrightError as exc:
            if "Executable doesn't exist" in str(exc):
                raise SystemExit(INSTALL_HINT) from None
            raise
        try:
            print_pdf(browser, html_path, pdf_path)
        finally:
            browser.close()
