"""Render the static site into an output directory."""

from __future__ import annotations

import hashlib
import io
import re
import shutil
from collections.abc import Callable
from pathlib import Path
from typing import Any

import segno
from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape
from markupsafe import Markup, escape

from sitegen import PACKAGE_DIR
from sitegen.content import Content

TEMPLATES_DIR = PACKAGE_DIR / "templates"
STATIC_DIR = PACKAGE_DIR / "static"
POSTER_PAGE = "affiche/index.html"

# Opening and closing quotation marks used by the content languages (guillemets, low-9, curly).
OPEN_QUOTES = "\u00ab\u201e\u201c\u2018\u201a"
CLOSE_QUOTES = "\u00bb\u201c\u201d\u2019\u2018"


def make_qr(url: str) -> tuple[str, bytes]:
    """Return the QR code as inline SVG and as PNG.

    Error correction level Q (25%) keeps it scannable on a dirty or damaged poster.
    """
    qr = segno.make_qr(url, error="q", boost_error=False)
    svg, png = io.BytesIO(), io.BytesIO()
    qr.save(svg, kind="svg", xmldecl=False, svgns=True, omitsize=True, border=4, nl=False)
    qr.save(png, kind="png", scale=20, border=4)
    return svg.getvalue().decode("utf-8"), png.getvalue()


def dutch_terms_filter(terms: list[str]) -> Callable[[str], Markup]:
    """Build the ``|nl`` template filter that marks literal Dutch terms in translated text.

    Each term gets ``<bdi lang="nl" dir="ltr">``: it reads correctly in right-to-left languages
    and screen readers pronounce it in Dutch. A quoted term (the text on the container screen)
    also stays on one line, quotes included. Text is escaped first, so content can't inject HTML.
    """
    if not terms:
        return escape
    alternatives = "|".join(re.escape(str(escape(t))) for t in sorted(terms, key=len, reverse=True))
    pattern = re.compile(f"([{OPEN_QUOTES}]?)({alternatives})([{CLOSE_QUOTES}]?)")

    def wrap(match: re.Match[str]) -> str:
        before, term, after = match.groups()
        marked = f'<bdi lang="nl" dir="ltr">{term}</bdi>'
        return f'<span class="nlq">{before}{marked}{after}</span>' if before or after else marked

    return lambda text: Markup(pattern.sub(wrap, str(escape(text))))  # noqa: S704 - escaped first


def _asset_version() -> str:
    """Short hash of the static files, so browsers fetch new CSS/JS only when it changed."""
    digest = hashlib.sha256()
    for path in sorted(p for p in STATIC_DIR.rglob("*") if p.is_file()):
        digest.update(path.read_bytes())
    return digest.hexdigest()[:10]


def _make_env(content: Content) -> Environment:
    env = Environment(
        loader=FileSystemLoader(TEMPLATES_DIR),
        autoescape=select_autoescape(["html"]),
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.filters["nl"] = dutch_terms_filter(content.site.get("dutch_terms", []))
    return env


def _language_summary(code: str, t: dict[str, Any]) -> dict[str, str]:
    """Return what the language chooser and the poster need to know about a language."""
    return {
        "code": code,
        "name": t["lang_name"],
        "dir": t["dir"],
        "choose_language": t["ui"]["choose_language"],
        "continue_in": t["ui"]["continue_in"],
        "poster_scan": t["poster_scan"],
        "poster_safe": t["poster_safe"],
    }


def build(content: Content, out_dir: Path) -> None:
    """Render every page, the poster and the QR code into ``out_dir`` (replacing what is there)."""
    site = content.site
    env = _make_env(content)
    common = {
        "site": site,
        "site_host": content.site_host,
        "langs": [_language_summary(code, content.langs[code]) for code in site["languages"]],
        "nl": content.langs["nl"],
        "en": content.langs["en"],
        "asset_version": _asset_version(),
    }

    if out_dir.exists():
        shutil.rmtree(out_dir)
    shutil.copytree(STATIC_DIR, out_dir / "static")

    def render(template: str, target: str, **ctx: Any) -> None:
        path = out_dir / target
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(env.get_template(template).render(**common, **ctx), encoding="utf-8")

    render("chooser.html", "index.html", lang="nl", dir="ltr", root="", not_found=False)
    # GitHub Pages serves /404.html for unknown URLs at any depth, so its links must be absolute.
    render("chooser.html", "404.html", lang="nl", dir="ltr", root=content.base_path, not_found=True)

    for code in site["languages"]:
        t = content.langs[code]
        render(
            "page.html",
            f"{code}/index.html",
            lang=code,
            dir=t["dir"],
            root="../",
            t=t,
            guide_url=site["sorting_guides"][code],
            fostplus_url=site["fostplus_sites"][code],
        )

    qr_svg, qr_png = make_qr(site["site_url"])
    (out_dir / "qr.svg").write_text(qr_svg, encoding="utf-8")
    (out_dir / "qr.png").write_bytes(qr_png)
    render(
        "poster.html",
        POSTER_PAGE,
        lang="nl",
        dir="ltr",
        root="../",
        p=content.poster,
        qr_svg=Markup(qr_svg),  # noqa: S704 - generated by segno,
    )
