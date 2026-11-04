"""The generated HTML: complete, safe, and with working internal links."""

from __future__ import annotations

import copy
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urldefrag, urlparse

import pytest

from sitegen.build import build
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
            if value is None:
                continue
            if name in ("href", "src"):
                self.links.append(value)
            elif name == "id":
                self.ids.add(value)


def _parse(page: Path) -> _LinkCollector:
    collector = _LinkCollector()
    collector.feed(page.read_text(encoding="utf-8"))
    return collector


def _pages(site: Path) -> list[Path]:
    return sorted(site.rglob("*.html"))


def test_every_language_and_special_page_is_built(content: Content, site: Path) -> None:
    expected = ["index.html", "404.html", "affiche/index.html", "qr.svg", "qr.png", "static/style.css"]
    expected += [f"{code}/index.html" for code in content.site["languages"]]
    assert [path for path in expected if not (site / path).is_file()] == []


def test_internal_links_and_anchors_resolve(content: Content, site: Path) -> None:
    broken = []
    for page in _pages(site):
        parsed = _parse(page)
        for link in parsed.links:
            if urlparse(link).scheme in ("http", "https", "mailto", "tel"):
                continue
            path, fragment = urldefrag(link.split("?")[0])
            if not path:  # same-page anchor
                if fragment and fragment not in parsed.ids:
                    broken.append(f"{page.relative_to(site)}: #{fragment}")
                continue
            base = site if path.startswith("/") else page.parent
            target = (base / path.lstrip("/")).resolve()
            if target.is_dir():
                target = target / "index.html"
            if not target.is_file():
                broken.append(f"{page.relative_to(site)}: {link}")
    assert broken == []


def test_404_uses_absolute_asset_paths(content: Content, site: Path) -> None:
    html = (site / "404.html").read_text()
    assert f'href="{content.base_path}static/style.css' in html


def test_poster_prints_the_url_the_qr_code_points_to(content: Content, site: Path) -> None:
    poster = (site / "affiche" / "index.html").read_text()
    assert content.site_host in poster
    assert (site / "qr.svg").read_text().startswith("<svg")


@pytest.mark.parametrize("code", ["nl", "ar"])
def test_quoted_screen_texts_stay_together_and_isolated(site: Path, code: str) -> None:
    html = (site / code / "index.html").read_text()
    assert '<bdi lang="nl" dir="ltr">Pas geaccepteerd.</bdi>' in html


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
