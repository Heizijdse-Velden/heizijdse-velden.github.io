"""What a visitor does in a real browser: choose a language, navigate, open answers.

Needs Chromium: `uv run playwright install chromium` (skipped locally if missing, required in CI).
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import pytest

from sitegen.content import Content

pytestmark = pytest.mark.e2e

PHONE = {"width": 390, "height": 844}
SMALL_PHONE = {"width": 320, "height": 640}


@pytest.fixture
def new_page(browser: Any) -> Iterator[Any]:
    """Factory for a fresh phone-sized page; every context is closed afterwards."""
    contexts = []

    def make(locale: str = "nl-BE", viewport: dict[str, int] = PHONE) -> Any:
        context = browser.new_context(locale=locale, viewport=viewport)
        contexts.append(context)
        return context.new_page()

    yield make
    for context in contexts:
        context.close()


def test_chooser_lists_every_language(content: Content, base_url: str, new_page: Any) -> None:
    page = new_page()
    page.goto(base_url + "/")
    codes = page.locator("a.lang-btn").evaluate_all("els => els.map(e => e.getAttribute('lang'))")
    assert codes == content.site["languages"]


def test_choosing_a_language_opens_that_page(content: Content, base_url: str, new_page: Any) -> None:
    page = new_page()
    page.goto(base_url + "/")
    page.locator('a.lang-btn[lang="tr"]').click()
    page.wait_for_url("**/tr/")
    assert page.locator("html").get_attribute("lang") == "tr"
    assert page.locator("h1").inner_text() == content.langs["tr"]["page_title"]


def test_other_language_button_returns_to_chooser(base_url: str, new_page: Any) -> None:
    page = new_page()
    page.goto(base_url + "/pl/")
    page.locator("a.lang-switch").click()
    page.wait_for_url(base_url + "/")
    assert page.locator("a.lang-btn").count() > 0


@pytest.mark.parametrize(("locale", "expected"), [("ro-RO", "ro"), ("ar-MA", "ar"), ("sw-KE", None)])
def test_chooser_suggests_the_phone_language(
    content: Content, base_url: str, new_page: Any, locale: str, expected: str | None
) -> None:
    page = new_page(locale=locale)
    page.goto(base_url + "/")
    visible = page.locator("a.suggest:visible")
    if expected is None:
        assert visible.count() == 0
    else:
        assert visible.count() == 1
        assert visible.get_attribute("data-lang") == expected
        assert visible.inner_text().strip() == content.langs[expected]["ui"]["continue_in"]


def test_arabic_page_reads_right_to_left(base_url: str, new_page: Any) -> None:
    page = new_page()
    page.goto(base_url + "/ar/")
    assert page.locator("html").get_attribute("dir") == "rtl"


def test_trust_message_is_visible_without_scrolling(content: Content, base_url: str, new_page: Any) -> None:
    for code in content.site["languages"]:
        page = new_page()
        page.goto(f"{base_url}/{code}/")
        box = page.locator(".trust").bounding_box()
        assert box is not None and box["y"] + box["height"] <= PHONE["height"], code


def test_quick_navigation_jumps_to_section(base_url: str, new_page: Any) -> None:
    page = new_page()
    page.goto(base_url + "/en/")
    page.locator('.quicknav a[href="#help"]').click()
    page.wait_for_url("**/en/#help")
    assert page.locator("#help").is_visible()
    assert page.evaluate("window.scrollY") > 0


def test_question_opens_with_call_button(base_url: str, new_page: Any) -> None:
    page = new_page()
    page.goto(base_url + "/nl/")
    question = page.locator("details#lost")
    assert question.get_attribute("open") is None
    question.locator("summary").click()
    assert question.get_attribute("open") is not None
    assert question.locator('a[href^="tel:"]').is_visible()


def test_unknown_url_shows_the_custom_404_page(base_url: str, new_page: Any) -> None:
    page = new_page()
    response = page.goto(base_url + "/does-not-exist/")
    assert response is not None and response.status == 404
    assert page.locator('link[rel="stylesheet"]').count() == 1
    assert page.locator("h1").is_visible()


def _all_pages(content: Content) -> list[str]:
    return ["/", "/affiche/", "/404.html"] + [f"/{code}/" for code in content.site["languages"]]


def test_no_console_errors_or_horizontal_scroll(content: Content, base_url: str, new_page: Any) -> None:
    """Console errors include Content-Security-Policy violations and missing files."""
    problems = []
    for path in _all_pages(content):
        page = new_page(viewport=SMALL_PHONE)
        errors: list[str] = []
        page.on(
            "console", lambda msg, errors=errors: errors.append(msg.text) if msg.type == "error" else None
        )
        page.on("pageerror", lambda exc, errors=errors: errors.append(str(exc)))
        page.goto(base_url + path)
        page.wait_for_load_state("networkidle")
        if errors:
            problems.append(f"{path}: {errors}")
        if path != "/affiche/":  # the poster is an A4 sheet by design
            overflow = page.evaluate("document.documentElement.scrollWidth - window.innerWidth")
            if overflow > 0:
                problems.append(f"{path}: {overflow}px horizontal scroll at 320px")
    assert problems == []
