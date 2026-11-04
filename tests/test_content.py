"""Content files: every language complete, every link well-formed."""

import copy

from sitegen.content import Content, all_links, validate


def test_all_translations_are_complete(content: Content) -> None:
    errors, _ = validate(content)
    assert errors == []


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
    assert any(e.startswith("tr.typo: unknown key") for e in errors)


def test_every_language_has_its_own_reference_links(content: Content) -> None:
    broken = copy.deepcopy(content)
    del broken.site["fostplus_sites"]["pl"]
    errors, _ = validate(broken)
    assert "site.json: fostplus_sites.pl is missing" in errors


def test_all_external_links_use_https(content: Content) -> None:
    assert [name for name, url in all_links(content.site) if not url.startswith("https://")] == []
