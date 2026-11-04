"""Render the static site into an output directory."""

from __future__ import annotations

import io
import re
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import segno
from jinja2 import Environment, FileSystemLoader, StrictUndefined, pass_context, select_autoescape
from markupsafe import Markup, escape

from sitegen import PACKAGE_DIR
from sitegen.content import Content

TEMPLATES_DIR = PACKAGE_DIR / "templates"
STATIC_DIR = PACKAGE_DIR / "static"

OPEN_QUOTES = "«„“‘‚"
CLOSE_QUOTES = "»“”’‘"


def make_qr(url: str) -> tuple[str, bytes]:
    """QR code as inline SVG and PNG. Error correction 'Q' (25%) survives a dirty or damaged poster."""
    qr = segno.make_qr(url, error="q", boost_error=False)
    svg, png = io.BytesIO(), io.BytesIO()
    qr.save(svg, kind="svg", xmldecl=False, svgns=True, omitsize=True, border=4, nl=False)
    qr.save(png, kind="png", scale=20, border=4)
    return svg.getvalue().decode("utf-8"), png.getvalue()


def _dutch_terms_filter(terms: list[str]):
    """Wrap literal Dutch terms (e.g. the text on the container screen) in <bdi lang="nl" dir="ltr">.

    This keeps them readable in right-to-left languages and makes screen readers pronounce them
    in Dutch. Text is escaped first, so translations can never inject HTML.
    """
    if not terms:
        pattern = None
    else:
        alternatives = "|".join(re.escape(str(escape(t))) for t in sorted(terms, key=len, reverse=True))
        pattern = re.compile(f"([{OPEN_QUOTES}]?)({alternatives})([{CLOSE_QUOTES}]?)")

    def wrap(match: re.Match[str]) -> str:
        before, term, after = match.groups()
        return f'<span class="nlq">{before}<bdi lang="nl" dir="ltr">{term}</bdi>{after}</span>'

    @pass_context
    def nl(ctx: Any, text: str) -> Markup:
        safe = str(escape(text))
        if ctx.get("lang") == "nl" or pattern is None:
            return Markup(safe)
        return Markup(pattern.sub(wrap, safe))

    return nl


def make_env(content: Content) -> Environment:
    env = Environment(
        loader=FileSystemLoader(TEMPLATES_DIR),
        autoescape=select_autoescape(["html"]),
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.filters["nl"] = _dutch_terms_filter(content.site.get("dutch_terms", []))
    return env


def _language_summary(code: str, t: dict[str, Any]) -> dict[str, str]:
    """What the language chooser and the poster need to know about each language."""
    return {
        "code": code,
        "name": t["lang_name"],
        "dir": t["dir"],
        "choose_language": t["ui"]["choose_language"],
        "continue_in": t["ui"]["continue_in"],
        "poster_scan": t["poster_scan"],
    }


def build(content: Content, out_dir: Path) -> None:
    site = content.site
    env = make_env(content)
    langs = [_language_summary(code, content.langs[code]) for code in site["languages"]]
    common = {
        "site": site,
        "site_host": content.site_host,
        "langs": langs,
        "build_id": datetime.now(UTC).strftime("%Y%m%d%H%M"),
    }

    if out_dir.exists():
        shutil.rmtree(out_dir)
    shutil.copytree(STATIC_DIR, out_dir / "static")
    shutil.copy(STATIC_DIR / "favicon.svg", out_dir / "favicon.svg")

    def render(template: str, target: str, **ctx: Any) -> None:
        path = out_dir / target
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(env.get_template(template).render(**common, **ctx), encoding="utf-8")

    # Language chooser.
    render("index.html", "index.html", lang="nl", dir="ltr", root="")

    # One page per language.
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
        )

    # Poster + QR code.
    qr_svg, qr_png = make_qr(site["site_url"])
    (out_dir / "qr.svg").write_text(qr_svg, encoding="utf-8")
    (out_dir / "qr.png").write_bytes(qr_png)
    render(
        "poster.html",
        "affiche/index.html",
        lang="nl",
        dir="ltr",
        root="../",
        p=content.poster,
        qr_svg=Markup(qr_svg),
        nl_scan=content.langs["nl"]["poster_scan"],
    )

    # GitHub Pages serves /404.html for unknown URLs at any depth, so asset paths must be absolute.
    render("404.html", "404.html", lang="nl", dir="ltr", root=content.base_path)
