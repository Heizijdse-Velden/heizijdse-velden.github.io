"""Render the poster page to an A4 PDF with headless Chromium (optional 'poster' dependency group)."""

from __future__ import annotations

from pathlib import Path

INSTALL_HINT = (
    "The poster needs Playwright. Install it once with:\n"
    "  uv run --group poster playwright install chromium\n"
    "and then run:\n"
    "  uv run --group poster sitegen poster"
)


def render_pdf(html_path: Path, pdf_path: Path) -> None:
    try:
        from playwright.sync_api import Error as PlaywrightError
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise SystemExit(INSTALL_HINT) from None

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(html_path.resolve().as_uri())
            page.emulate_media(media="print")
            page.pdf(
                path=str(pdf_path),
                format="A4",
                print_background=True,
                margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
                prefer_css_page_size=True,
            )
            browser.close()
    except PlaywrightError as exc:
        if "Executable doesn't exist" in str(exc):
            raise SystemExit(INSTALL_HINT) from None
        raise
