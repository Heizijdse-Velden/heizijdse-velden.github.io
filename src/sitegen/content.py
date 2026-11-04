"""Load and validate the content files in ``content/``."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

REFERENCE_LANG = "nl"
#: Languages the language chooser itself is written in (title, trust message, footer).
CHOOSER_LANGS = ("nl", "en")
PER_LANGUAGE_LINKS = ("sorting_guides", "fostplus_sites")
REQUIRED_SITE_KEYS = (
    "site_url",
    "languages",
    "last_reviewed",
    "publisher",
    "contacts",
    "links",
    *PER_LANGUAGE_LINKS,
)


class ContentError(Exception):
    """A content file can't be read, e.g. a JSON syntax error after a manual edit."""


@dataclass
class Content:
    """Everything in ``content/``: site settings, one dict per language, and the poster texts."""

    site: dict[str, Any]
    langs: dict[str, dict[str, Any]]
    poster: dict[str, Any]

    @property
    def site_host(self) -> str:
        """Site address without scheme, as printed under the QR code."""
        url = urlparse(str(self.site["site_url"]))
        return url.netloc + url.path.rstrip("/")

    @property
    def base_path(self) -> str:
        """URL path the site is served from: ``/`` for user/org sites, ``/repo/`` for project sites."""
        return urlparse(str(self.site["site_url"])).path or "/"


def all_links(site: dict[str, Any]) -> list[tuple[str, str]]:
    """Return every external link in site.json as ``(name, url)``, e.g. ``('links.mijndiftar', ...)``."""
    pairs = [(f"links.{name}", url) for name, url in site["links"].items()]
    for group in PER_LANGUAGE_LINKS:
        pairs += [(f"{group}.{code}", url) for code, url in site[group].items()]
    return pairs


def _read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ContentError(f"{path}: file not found") from None
    except json.JSONDecodeError as exc:
        raise ContentError(f"{path}, line {exc.lineno}, column {exc.colno}: {exc.msg}") from None
    if not isinstance(data, dict):
        raise ContentError(f"{path}: expected a JSON object")
    return data


def load_content(content_dir: Path) -> Content:
    """Read all content files. Missing language files are reported by :func:`validate`."""
    site = _read_json(content_dir / "site.json")
    langs = {
        code: _read_json(path)
        for code in site.get("languages", [])
        if (path := content_dir / "lang" / f"{code}.json").exists()
    }
    return Content(site=site, langs=langs, poster=_read_json(content_dir / "poster.json"))


def _compare_structure(ref: Any, other: Any, path: str, errors: list[str]) -> None:
    """Every language must have exactly the same keys (and list lengths) as the reference language."""
    if isinstance(ref, dict):
        if not isinstance(other, dict):
            errors.append(f"{path}: expected an object")
            return
        errors += [f"{path}.{key}: missing" for key in sorted(ref.keys() - other.keys())]
        errors += [
            f"{path}.{key}: unknown key (not in {REFERENCE_LANG}.json)"
            for key in sorted(other.keys() - ref.keys())
        ]
        for key in ref.keys() & other.keys():
            _compare_structure(ref[key], other[key], f"{path}.{key}", errors)
    elif isinstance(ref, list):
        if not isinstance(other, list) or len(other) != len(ref):
            errors.append(f"{path}: expected a list of {len(ref)} items")
            return
        for i, (a, b) in enumerate(zip(ref, other, strict=True)):
            _compare_structure(a, b, f"{path}[{i}]", errors)
    elif isinstance(ref, str) and not isinstance(other, str):
        errors.append(f"{path}: expected text")


def _find_empty(value: Any, path: str, errors: list[str], allowed: set[str]) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            _find_empty(child, f"{path}.{key}", errors, allowed)
    elif isinstance(value, list):
        for i, child in enumerate(value):
            _find_empty(child, f"{path}[{i}]", errors, allowed)
    elif isinstance(value, str) and not value.strip() and path not in allowed:
        errors.append(f"{path}: is empty")


def _validate_language(content: Content, code: str, errors: list[str]) -> None:
    lang = content.langs.get(code)
    if lang is None:
        errors.append(f"content/lang/{code}.json is missing")
        return
    _compare_structure(content.langs[REFERENCE_LANG], lang, code, errors)
    _find_empty(lang, code, errors, allowed={f"{REFERENCE_LANG}.translation_note"})
    if lang.get("dir") not in ("ltr", "rtl"):
        errors.append(f"{code}.dir must be 'ltr' or 'rtl'")
    if lang.get("is_translation") is not (code != REFERENCE_LANG):
        errors.append(f"{code}.is_translation must be {str(code != REFERENCE_LANG).lower()}")
    errors += [
        f"site.json: {group}.{code} is missing"
        for group in PER_LANGUAGE_LINKS
        if code not in content.site[group]
    ]


def validate(content: Content) -> tuple[list[str], list[str]]:
    """Check the content. Return ``(errors, warnings)``: errors block the build, warnings don't."""
    site = content.site
    missing = [key for key in REQUIRED_SITE_KEYS if key not in site]
    if missing:
        return [f"site.json: missing {', '.join(missing)}"], []

    errors = [
        f"site.json: '{code}' must be in languages (the language chooser uses it)"
        for code in CHOOSER_LANGS
        if code not in site["languages"]
    ]
    if REFERENCE_LANG not in content.langs:
        errors.append(
            f"content/lang/{REFERENCE_LANG}.json is missing (all other languages are compared to it)"
        )
    if errors:
        return errors, []
    for code in site["languages"]:
        _validate_language(content, code, errors)

    url = site["site_url"]
    if not url.startswith("https://") or not url.endswith("/"):
        errors.append("site.json: site_url must start with https:// and end with /")
    errors += [
        f"site.json: {name} must start with https://"
        for name, link in all_links(site)
        if not link.startswith("https://")
    ]

    warnings = []
    if not site["publisher"].strip():
        warnings.append("site.json: 'publisher' (V.U.) is empty; it is required on printed posters.")
    return errors, warnings
