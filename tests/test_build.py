"""The generated site: complete, safe, and with working internal links."""

from __future__ import annotations

import copy
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urldefrag, urlparse

import pytest

from sitegen.build import build, dutch_terms_filter, make_qr
from sitegen.content import Content

EXTERNAL_RESOURCE = re.compile(
    r'<(?:script|img)\b[^>]*\bsrc="https?:'
    r'|<link\b(?=[^>]*\brel="(?:stylesheet|icon|preload|modulepreload)")[^>]*\bhref="https?:'
)


class _LinkCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []
        self.ids: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        for name, value in attrs:
            if value is not None and name in ("href", "src"):
                self.links.append(value)
            elif value is not None and name == "id":
                self.ids.add(value)


def _parse(page: Path) -> _LinkCollector:
    collector = _LinkCollector()
    collector.feed(page.read_text(encoding="utf-8"))
    return collector


def _pages(site: Path) -> list[Path]:
    return sorted(site.rglob("*.html"))


def _visible_text(html: str) -> str:
    html = re.sub(r"<(script|style|svg)\b.*?</\1>", " ", html, flags=re.S)
    return re.sub(r"<[^>]+>", "", html)


def test_every_language_and_special_page_is_built(content: Content, site: Path) -> None:
    expected = ["index.html", "404.html", "affiche/index.html", "qr.svg", "qr.png", "static/style.css"]
    expected += [f"{code}/index.html" for code in content.site["languages"]]
    assert [path for path in expected if not (site / path).is_file()] == []


def test_internal_links_and_anchors_resolve(site: Path) -> None:
    broken = []
    for page in _pages(site):
        parsed = _parse(page)
        for link in parsed.links:
            if urlparse(link).scheme in ("http", "https", "mailto", "tel"):
                continue
            path, fragment = urldefrag(link.split("?")[0])
            if not path:  # same-page anchor
                if fragment not in parsed.ids:
                    broken.append(f"{page.relative_to(site)}: #{fragment}")
                continue
            target = ((site if path.startswith("/") else page.parent) / path.lstrip("/")).resolve()
            if not (target / "index.html" if target.is_dir() else target).is_file():
                broken.append(f"{page.relative_to(site)}: {link}")
    assert broken == []


def test_404_page_offers_every_language_with_absolute_links(content: Content, site: Path) -> None:
    html = (site / "404.html").read_text()
    assert f'href="{content.base_path}static/style.css' in html
    for code in content.site["languages"]:
        assert f'href="{content.base_path}{code}/"' in html


def test_build_is_reproducible(content: Content, site: Path, tmp_path: Path) -> None:
    build(content, tmp_path)
    for page in _pages(site):
        assert (tmp_path / page.relative_to(site)).read_text() == page.read_text(), page


def test_qr_code_encodes_the_site_url_printed_on_the_poster(content: Content, site: Path) -> None:
    svg, png = make_qr(content.site["site_url"])
    assert svg.startswith("<svg")
    assert png.startswith(b"\x89PNG")
    assert content.site_host in (site / "affiche" / "index.html").read_text()


def test_dutch_terms_are_isolated_and_quoted_ones_kept_together() -> None:
    mark = dutch_terms_filter(["Pas geaccepteerd.", "toegangspas"])
    html = str(mark("Toon “Pas geaccepteerd.” en je toegangspas <b>"))
    assert '<span class="nlq">“<bdi lang="nl" dir="ltr">Pas geaccepteerd.</bdi>”</span>' in html
    assert '<bdi lang="nl" dir="ltr">toegangspas</bdi>' in html
    assert "&lt;b&gt;" in html
    assert str(dutch_terms_filter([])("<b>")) == "&lt;b&gt;"


def test_translated_text_is_escaped(content: Content, tmp_path: Path) -> None:
    hostile = copy.deepcopy(content)
    hostile.langs["en"]["intro"] = '<script>alert("x")</script> restafval'
    build(hostile, tmp_path)
    html = (tmp_path / "en" / "index.html").read_text()
    assert "<script>alert" not in html
    assert "&lt;script&gt;" in html


def test_pages_respect_the_content_security_policy(site: Path) -> None:
    """No inline scripts, style attributes or external resources: the CSP only allows the site itself."""
    for page in _pages(site):
        html = page.read_text()
        assert "Content-Security-Policy" in html, page
        assert not re.search(r"<script(?![^>]*\bsrc=)", html), page
        assert " style=" not in html, page
        assert not EXTERNAL_RESOURCE.search(html), page


@pytest.mark.parametrize(
    ("pattern", "problem"),
    [
        # Plain spaces only: French correctly uses no-break spaces before ? ! : ;
        (r" {2,}", "double space"),
        (r" [,.;:!?](?: |$)", "space before punctuation"),
        (r"\( | \)", "space inside brackets"),
    ],
)
def test_no_stray_spaces_in_visible_text(site: Path, pattern: str, problem: str) -> None:
    offenders = []
    for page in _pages(site):
        for line in _visible_text(page.read_text()).splitlines():
            text = line.strip()
            if text and re.search(pattern, text):
                offenders.append(f"{page.relative_to(site)}: {text[:80]!r}")
    assert offenders == [], problem
