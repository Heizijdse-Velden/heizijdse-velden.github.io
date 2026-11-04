import copy
import re
from pathlib import Path

import pytest

from sitegen import CONTENT_DIR
from sitegen.build import build
from sitegen.content import Content, load_content, validate


@pytest.fixture(scope="module")
def content() -> Content:
    return load_content(CONTENT_DIR)


@pytest.fixture(scope="module")
def site(content: Content, tmp_path_factory: pytest.TempPathFactory) -> Path:
    out = tmp_path_factory.mktemp("site")
    build(content, out)
    return out


def test_all_translations_are_complete(content: Content) -> None:
    errors, _ = validate(content)
    assert errors == []


def test_missing_or_extra_keys_are_reported(content: Content) -> None:
    broken = copy.deepcopy(content)
    del broken.langs["tr"]["faq"]["bag"]
    broken.langs["tr"]["steps"].pop()
    broken.langs["tr"]["safety"] = " "
    broken.langs["tr"]["typo"] = "x"
    errors, _ = validate(broken)
    assert "tr.faq.bag: missing" in errors
    assert "tr.steps: expected a list of 6 items" in errors
    assert "tr.safety: is empty" in errors
    assert any(e.startswith("tr.typo: unknown key") for e in errors)


def test_every_language_and_special_page_is_built(content: Content, site: Path) -> None:
    expected = ["index.html", "404.html", "affiche/index.html", "qr.svg", "qr.png", "static/style.css"]
    expected += [f"{code}/index.html" for code in content.site["languages"]]
    missing = [path for path in expected if not (site / path).is_file()]
    assert missing == []


def test_404_uses_absolute_asset_paths(content: Content, site: Path) -> None:
    html = (site / "404.html").read_text()
    assert f'href="{content.base_path}static/style.css' in html


def test_qr_code_and_printed_url_match_site_url(content: Content, site: Path) -> None:
    poster = (site / "affiche" / "index.html").read_text()
    assert content.site_host in poster
    assert (site / "qr.svg").read_text().startswith("<svg")


def test_dutch_terms_are_isolated_in_rtl_pages(site: Path) -> None:
    html = (site / "ar" / "index.html").read_text()
    assert '<bdi lang="nl" dir="ltr">pas geaccepteerd</bdi>' in html


def test_translated_text_is_escaped(content: Content, tmp_path: Path) -> None:
    hostile = copy.deepcopy(content)
    hostile.langs["en"]["intro"] = '<script>alert("x")</script> restafval'
    build(hostile, tmp_path)
    html = (tmp_path / "en" / "index.html").read_text()
    assert "<script>alert" not in html
    assert "&lt;script&gt;" in html


def test_pages_respect_the_content_security_policy(site: Path) -> None:
    """No inline scripts or style attributes: the CSP only allows files from the site itself."""
    for page in site.rglob("*.html"):
        html = page.read_text()
        assert not re.search(r"<script(?![^>]*\bsrc=)", html), page
        assert " style=" not in html, page
