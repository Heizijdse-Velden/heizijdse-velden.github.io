"""Content files: every language complete, every setting present, every link well-formed."""

from __future__ import annotations

import copy
import json
import shutil
from collections.abc import Callable
from pathlib import Path

import pytest

from sitegen import CONTENT_DIR
from sitegen.content import Content, ContentError, all_links, load_content, validate


def test_real_content_is_valid(content: Content) -> None:
    assert validate(content) == ([], [])


def test_missing_empty_or_unknown_keys_are_reported(content: Content) -> None:
    broken = copy.deepcopy(content)
    del broken.langs["tr"]["faq"]["bag"]
    broken.langs["tr"]["steps"].pop()
    broken.langs["tr"]["trust"] = " "
    broken.langs["tr"]["typo"] = "x"
    errors, _ = validate(broken)
    assert "tr.faq.bag: missing" in errors
    assert "tr.steps: expected a list of 6 items" in errors
    assert "tr.trust: is empty" in errors
    assert "tr.typo: unknown key (not in nl.json)" in errors


@pytest.mark.parametrize(
    ("change", "expected"),
    [
        (lambda c: c.langs["pl"].update(dir="up"), "pl.dir must be 'ltr' or 'rtl'"),
        (lambda c: c.langs["pl"].update(is_translation=False), "pl.is_translation must be true"),
        (lambda c: c.langs["pl"].update(ui="text"), "pl.ui: expected an object"),
        (lambda c: c.langs["pl"].update(intro=["text"]), "pl.intro: expected text"),
        (lambda c: c.langs.pop("pl"), "content/lang/pl.json is missing"),
        (lambda c: c.site["fostplus_sites"].pop("pl"), "site.json: fostplus_sites.pl is missing"),
        (
            lambda c: c.site.update(site_url="http://x.be"),
            "site.json: site_url must start with https:// and end with /",
        ),
        (
            lambda c: c.site["links"].update(iok_video="http://x.be"),
            "site.json: links.iok_video must start with https://",
        ),
        (lambda c: c.site.pop("contacts"), "site.json: missing contacts"),
        (
            lambda c: c.site["languages"].remove("en"),
            "site.json: 'en' must be in languages (the language chooser uses it)",
        ),
        (
            lambda c: c.langs.pop("nl"),
            "content/lang/nl.json is missing (all other languages are compared to it)",
        ),
    ],
)
def test_broken_content_is_reported(
    content: Content, change: Callable[[Content], object], expected: str
) -> None:
    broken = copy.deepcopy(content)
    change(broken)
    errors, _ = validate(broken)
    assert expected in errors


def test_empty_publisher_is_a_warning_not_an_error(content: Content) -> None:
    unsigned = copy.deepcopy(content)
    unsigned.site["publisher"] = ""
    errors, warnings = validate(unsigned)
    assert errors == []
    assert warnings == ["site.json: 'publisher' (V.U.) is empty; it is required on printed posters."]


def test_json_syntax_error_names_file_and_line(tmp_path: Path) -> None:
    shutil.copytree(CONTENT_DIR, tmp_path, dirs_exist_ok=True)
    (tmp_path / "lang" / "fr.json").write_text('{\n  "dir": "ltr",\n}\n', encoding="utf-8")
    with pytest.raises(ContentError, match=r"fr\.json, line 3, column 1"):
        load_content(tmp_path)


def test_missing_file_and_non_object_are_reported(tmp_path: Path) -> None:
    with pytest.raises(ContentError, match=r"site\.json: file not found"):
        load_content(tmp_path)
    (tmp_path / "site.json").write_text(json.dumps(["not", "an", "object"]), encoding="utf-8")
    with pytest.raises(ContentError, match=r"site\.json: expected a JSON object"):
        load_content(tmp_path)


def test_all_links_lists_every_external_link_once_per_name(content: Content) -> None:
    names = [name for name, _ in all_links(content.site)]
    assert len(names) == len(set(names))
    assert "links.mijndiftar" in names
    assert "sorting_guides.ar" in names
