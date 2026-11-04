"""Loading and validating the content files in content/."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

REFERENCE_LANG = "nl"
PER_LANGUAGE_LINKS = ("sorting_guides", "fostplus_sites")


@dataclass
class Content:
    site: dict[str, Any]
    langs: dict[str, dict[str, Any]]
    poster: dict[str, Any]

    @property
    def site_host(self) -> str:
        """Site address without scheme, as printed under the QR code."""
        url = urlparse(self.site["site_url"])
        return url.netloc + url.path.rstrip("/")

    @property
    def base_path(self) -> str:
        """URL path the site is served from ('/' for user/org sites, '/repo/' for project sites)."""
        return urlparse(self.site["site_url"]).path or "/"


def all_links(site: dict[str, Any]) -> list[tuple[str, str]]:
    """Every external link in site.json as (name, url), e.g. ('links.mijndiftar', 'https://...')."""
    pairs = [(f"links.{name}", url) for name, url in site["links"].items()]
    for group in PER_LANGUAGE_LINKS:
        pairs += [(f"{group}.{code}", url) for code, url in site[group].items()]
    return pairs


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_content(content_dir: Path) -> Content:
    site = _read_json(content_dir / "site.json")
    langs = {
        code: _read_json(path)
        for code in site["languages"]
        if (path := content_dir / "lang" / f"{code}.json").exists()
    }
    poster = _read_json(content_dir / "poster.json")
    return Content(site=site, langs=langs, poster=poster)


def _compare_structure(ref: Any, other: Any, path: str, errors: list[str]) -> None:
    """Every language must have exactly the same keys (and list lengths) as the reference language."""
    if isinstance(ref, dict):
        if not isinstance(other, dict):
            errors.append(f"{path}: expected an object")
            return
        for key in ref.keys() - other.keys():
            errors.append(f"{path}.{key}: missing")
        for key in other.keys() - ref.keys():
            errors.append(f"{path}.{key}: unknown key (not in {REFERENCE_LANG}.json)")
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


def validate(content: Content) -> tuple[list[str], list[str]]:
    """Return (errors, warnings). Errors block the build; warnings don't."""
    errors: list[str] = []
    warnings: list[str] = []
    site = content.site
    ref = content.langs.get(REFERENCE_LANG)
    if ref is None:
        return [f"content/lang/{REFERENCE_LANG}.json is missing"], warnings

    for code in site["languages"]:
        lang = content.langs.get(code)
        if lang is None:
            errors.append(f"content/lang/{code}.json is missing")
            continue
        _compare_structure(ref, lang, code, errors)
        _find_empty(lang, code, errors, allowed={f"{REFERENCE_LANG}.translation_note"})
        if lang.get("dir") not in ("ltr", "rtl"):
            errors.append(f"{code}.dir must be 'ltr' or 'rtl'")
        if code != REFERENCE_LANG and lang.get("is_translation") is not True:
            errors.append(f"{code}.is_translation must be true")
        for per_language in PER_LANGUAGE_LINKS:
            if code not in site[per_language]:
                errors.append(f"site.json: {per_language}.{code} is missing")

    url = site["site_url"]
    if not url.startswith("https://") or not url.endswith("/"):
        errors.append("site.json: site_url must start with https:// and end with /")
    for name, link in all_links(site):
        if not link.startswith("https://"):
            errors.append(f"site.json: {name} must start with https://")
    if not site.get("publisher", "").strip():
        warnings.append("site.json: 'publisher' (V.U.) is empty; it is required on printed posters.")
    return errors, warnings
