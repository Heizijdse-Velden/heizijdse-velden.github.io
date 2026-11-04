"""What a visitor does in a real browser: choose a language, navigate, open answers. And the poster PDF.

Needs Chromium: ``uv run playwright install chromium`` (skipped locally if missing, required in CI).
"""

from __future__ import annotations

import re
from collections.abc import Callable, Iterator
from pathlib import Path

import pytest
from playwright.sync_api import Browser, BrowserContext, Page, ViewportSize

from sitegen.content import Content
from sitegen.poster import print_pdf

pytestmark = pytest.mark.e2e

PHONE: ViewportSize = {"width": 390, "height": 844}
SMALL_PHONE: ViewportSize = {"width": 320, "height": 640}

NewPage = Callable[..., Page]


@pytest.fixture
def new_page(browser: Browser) -> Iterator[NewPage]:
    """Make fresh phone-sized pages; their contexts are closed afterwards."""
    contexts: list[BrowserContext] = []

    def make(locale: str = "nl-BE", viewport: ViewportSize = PHONE) -> Page:
        context = browser.new_context(locale=locale, viewport=viewport)
        contexts.append(context)
        return context.new_page()

    yield make
    for context in contexts:
        context.close()


def test_chooser_lists_every_language(content: Content, base_url: str, new_page: NewPage) -> None:
    page = new_page()
    page.goto(base_url + "/")
    codes = page.locator("a.lang-btn").evaluate_all("links => links.map(link => link.lang)")
    assert codes == content.site["languages"]


def test_choosing_a_language_opens_that_page(content: Content, base_url: str, new_page: NewPage) -> None:
    page = new_page()
    page.goto(base_url + "/")
    page.locator('a.lang-btn[lang="tr"]').click()
    page.wait_for_url("**/tr/")
    assert page.locator("html").get_attribute("lang") == "tr"
    assert page.locator("h1").inner_text() == content.langs["tr"]["page_title"]


def test_other_language_button_returns_to_chooser(base_url: str, new_page: NewPage) -> None:
    page = new_page()
    page.goto(base_url + "/pl/")
    page.locator("a.lang-switch").click()
    page.wait_for_url(base_url + "/")
    assert page.locator("a.lang-btn").count() > 0


@pytest.mark.parametrize(("locale", "expected"), [("ro-RO", "ro"), ("ar-MA", "ar"), ("sw-KE", None)])
def test_chooser_suggests_the_phone_language(
    content: Content, base_url: str, new_page: NewPage, locale: str, expected: str | None
) -> None:
    page = new_page(locale=locale)
    page.goto(base_url + "/")
    visible = page.locator("a.suggest:visible")
    if expected is None:
        assert visible.count() == 0
    else:
        assert visible.get_attribute("data-lang") == expected
        assert visible.inner_text().strip() == content.langs[expected]["ui"]["continue_in"]


def test_arabic_page_reads_right_to_left(base_url: str, new_page: NewPage) -> None:
    page = new_page()
    page.goto(base_url + "/ar/")
    assert page.locator("html").get_attribute("dir") == "rtl"


def test_trust_message_is_visible_without_scrolling(
    content: Content, base_url: str, new_page: NewPage
) -> None:
    for path in ["/", *(f"/{code}/" for code in content.site["languages"])]:
        page = new_page()
        page.goto(base_url + path)
        box = page.locator(".trust").bounding_box()
        assert box is not None, path
        assert box["y"] + box["height"] <= PHONE["height"], path


def test_quick_navigation_jumps_to_section(base_url: str, new_page: NewPage) -> None:
    page = new_page()
    page.goto(base_url + "/en/")
    page.locator('.quicknav a[href="#help"]').click()
    page.wait_for_url("**/en/#help")
    assert page.locator("#help").is_visible()
    assert page.evaluate("window.scrollY") > 0


def test_question_opens_with_call_button(base_url: str, new_page: NewPage) -> None:
    page = new_page()
    page.goto(base_url + "/nl/")
    question = page.locator("details#lost")
    assert question.get_attribute("open") is None
    question.locator("summary").click()
    assert question.get_attribute("open") is not None
    assert question.locator('a[href^="tel:"]').is_visible()


def test_wrong_url_leads_to_every_language_in_one_tap(base_url: str, new_page: NewPage) -> None:
    page = new_page()
    response = page.goto(base_url + "/old/link/")
    assert response is not None
    assert response.status == 404
    assert page.locator(".not-found").is_visible()
    page.locator('a.lang-btn[lang="fr"]').click()
    page.wait_for_url(base_url + "/fr/")


def _watch_errors(page: Page) -> list[str]:
    """Collect console errors (incl. Content-Security-Policy violations, missing files) and crashes."""
    errors: list[str] = []
    page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)
    page.on("pageerror", lambda exc: errors.append(str(exc)))
    return errors


def test_no_console_errors_or_horizontal_scroll(content: Content, base_url: str, new_page: NewPage) -> None:
    problems = []
    for path in ["/", "/404.html", "/affiche/", *(f"/{code}/" for code in content.site["languages"])]:
        page = new_page(viewport=SMALL_PHONE)
        errors = _watch_errors(page)
        page.goto(base_url + path)
        page.wait_for_load_state("networkidle")
        if errors:
            problems.append(f"{path}: {errors}")
        overflow = page.evaluate("document.documentElement.scrollWidth - window.innerWidth")
        if path != "/affiche/" and overflow > 0:  # the poster is an A4 sheet by design
            problems.append(f"{path}: {overflow}px horizontal scroll at 320px")
    assert problems == []


def test_poster_prints_as_a_single_a4_page(site: Path, browser: Browser, tmp_path: Path) -> None:
    pdf = tmp_path / "out" / "affiche.pdf"
    print_pdf(browser, site / "affiche" / "index.html", pdf)
    data = pdf.read_bytes()
    assert data.startswith(b"%PDF")
    assert len(re.findall(rb"/Type\s*/Page\b", data)) == 1
    assert re.search(rb"/MediaBox\s*\[\s*0 0 59[45]\.\d+ 84[12]\.\d+\s*\]", data), "not A4"
