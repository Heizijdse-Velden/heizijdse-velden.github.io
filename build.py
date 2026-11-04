#!/usr/bin/env python3
"""Bouwt de statische site naar _site/.

Gebruik:
    python build.py            # bouwen
    python build.py --check    # alleen controleren (vertalingen volledig? links ok?)

Bronnen:
    site.json          algemene instellingen (URL, talen, contactgegevens, links)
    content/<taal>.json  alle teksten per taal (zelfde sleutels als nl.json)
    content/poster.json  teksten voor de affiche
    templates/         HTML-sjablonen (Jinja2)
    static/            CSS, JavaScript, favicon
"""
from __future__ import annotations

import io
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import segno
from jinja2 import Environment, FileSystemLoader, StrictUndefined, pass_context, select_autoescape
from markupsafe import Markup, escape

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "_site"


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------- controles
def compare_structure(ref, other, path, errors):
    """Elke taal moet exact dezelfde sleutels hebben als nl.json."""
    if isinstance(ref, dict):
        if not isinstance(other, dict):
            errors.append(f"{path}: verwacht een object")
            return
        for k in ref:
            if k.startswith("_"):
                continue
            if k not in other:
                errors.append(f"{path}.{k}: ontbreekt")
            else:
                compare_structure(ref[k], other[k], f"{path}.{k}", errors)
        for k in other:
            if k not in ref and not k.startswith("_"):
                errors.append(f"{path}.{k}: onbekende sleutel (staat niet in nl.json)")
    elif isinstance(ref, list):
        if not isinstance(other, list) or len(other) != len(ref):
            errors.append(f"{path}: verwacht een lijst met {len(ref)} items")
            return
        for i, (a, b) in enumerate(zip(ref, other)):
            compare_structure(a, b, f"{path}[{i}]", errors)
    elif isinstance(ref, str):
        if not isinstance(other, str):
            errors.append(f"{path}: verwacht tekst")


def find_empty(obj, path, errors, allow=()):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if not k.startswith("_"):
                find_empty(v, f"{path}.{k}", errors, allow)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            find_empty(v, f"{path}[{i}]", errors, allow)
    elif isinstance(obj, str) and not obj.strip() and path not in allow:
        errors.append(f"{path}: is leeg")


def validate(site: dict, content: dict[str, dict]) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    ref = content["nl"]
    for code in site["languages"]:
        t = content.get(code)
        if t is None:
            errors.append(f"content/{code}.json ontbreekt")
            continue
        compare_structure(ref, t, code, errors)
        find_empty(t, code, errors, allow={"nl.translation_note"})
        if t.get("dir") not in ("ltr", "rtl"):
            errors.append(f"{code}.dir moet 'ltr' of 'rtl' zijn")
        if code != "nl" and not t.get("is_translation"):
            errors.append(f"{code}.is_translation moet true zijn")
        if code not in site["sorting_guides"]:
            errors.append(f"site.json: sorting_guides.{code} ontbreekt")

    url = urlparse(site["site_url"])
    if url.scheme != "https" or not url.netloc:
        errors.append("site.json: site_url moet met https:// beginnen")
    if not site["site_url"].endswith("/"):
        errors.append("site.json: site_url moet eindigen op /")
    for name, link in {**site["links"], **site["sorting_guides"]}.items():
        if not str(link).startswith("https://"):
            errors.append(f"site.json: link {name} moet met https:// beginnen")
    if not site.get("publisher", "").strip():
        warnings.append("site.json: 'publisher' (V.U.) is leeg; verplicht op gedrukte affiches.")
    return errors, warnings


# ---------------------------------------------------------------- QR
def make_qr(url: str) -> tuple[str, bytes]:
    # Foutcorrectie 'q' (25%): blijft leesbaar als de affiche wat vuil of beschadigd raakt.
    qr = segno.make_qr(url, error="q", boost_error=False)
    svg_buf = io.BytesIO()
    qr.save(svg_buf, kind="svg", xmldecl=False, svgns=True, omitsize=True,
            border=4, dark="#000000", light="#ffffff", nl=False)
    png_buf = io.BytesIO()
    qr.save(png_buf, kind="png", scale=20, border=4)
    return svg_buf.getvalue().decode("utf-8"), png_buf.getvalue()


# ---------------------------------------------------------------- build
def main() -> int:
    check_only = "--check" in sys.argv
    site = load_json(ROOT / "site.json")
    content = {}
    for code in site["languages"]:
        p = ROOT / "content" / f"{code}.json"
        if p.exists():
            content[code] = load_json(p)
    poster = load_json(ROOT / "content" / "poster.json")

    errors, warnings = validate(site, content)
    for w in warnings:
        print(f"LET OP: {w}")
    if errors:
        print("FOUTEN — de site is niet gebouwd:")
        for e in errors:
            print(f"  - {e}")
        return 1
    if check_only:
        print(f"OK: {len(content)} talen gecontroleerd.")
        return 0

    env = Environment(
        loader=FileSystemLoader(ROOT / "templates"),
        autoescape=select_autoescape(["html"]),
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
    )

    # Nederlandse termen in vertaalde teksten (bv. wat er op het scherm staat) krijgen
    # <bdi lang="nl" dir="ltr">: correcte weergave in het Arabisch (rechts-naar-links)
    # en Nederlandse uitspraak in schermlezers. Eerst escapen, dan pas markeren: veilig.
    terms = sorted(site.get("dutch_terms", []), key=len, reverse=True)
    quotes_open, quotes_close = "«„“‘‚", "»“”’‘"
    term_re = re.compile(
        f"([{quotes_open}]?)(" + "|".join(re.escape(str(escape(x))) for x in terms) + f")([{quotes_close}]?)"
    ) if terms else None

    @pass_context
    def nl_filter(ctx, text):
        safe = str(escape(text))
        if ctx.get("lang") == "nl" or term_re is None:
            return Markup(safe)
        # Aanhalingstekens + term blijven samen op één regel (class="nlq").
        return Markup(term_re.sub(
            lambda m: f'<span class="nlq">{m.group(1)}<bdi lang="nl" dir="ltr">{m.group(2)}</bdi>{m.group(3)}</span>',
            safe))

    env.filters["nl"] = nl_filter
    site_host = urlparse(site["site_url"]).netloc + urlparse(site["site_url"]).path.rstrip("/")
    build_id = datetime.now(timezone.utc).strftime("%Y%m%d%H%M")
    langs = [
        {
            "code": code,
            "name": content[code]["lang_name"],
            "dir": content[code]["dir"],
            "choose_language": content[code]["ui"]["choose_language"],
            "continue_in": content[code]["ui"]["continue_in"],
            "poster_scan": content[code]["poster_scan"],
        }
        for code in site["languages"]
    ]
    common = {"site": site, "site_host": site_host, "langs": langs, "build_id": build_id}

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    shutil.copytree(ROOT / "static", OUT / "static")
    shutil.copy(ROOT / "static" / "favicon.svg", OUT / "favicon.svg")

    def write(rel: str, html: str):
        target = OUT / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(html, encoding="utf-8")

    # Taalkiezer
    write("index.html", env.get_template("index.html").render(
        **common, lang="nl", dir="ltr", root=""))

    # Eén pagina per taal
    page = env.get_template("page.html")
    for code in site["languages"]:
        t = content[code]
        write(f"{code}/index.html", page.render(
            **common, lang=code, dir=t["dir"], root="../", t=t,
            guide_url=site["sorting_guides"][code]))

    # Affiche + QR
    qr_svg, qr_png = make_qr(site["site_url"])
    (OUT / "qr.svg").write_text(qr_svg, encoding="utf-8")
    (OUT / "qr.png").write_bytes(qr_png)
    write("affiche/index.html", env.get_template("poster.html").render(
        **common, lang="nl", dir="ltr", root="../", p=poster, qr_svg=qr_svg,
        nl_scan=content["nl"]["poster_scan"]))

    # 404 → terug naar de taalkiezer
    write("404.html", env.get_template("404.html").render(
        **common, lang="nl", dir="ltr", root=urlparse(site["site_url"]).path))

    print(f"Klaar: {len(site['languages'])} talen → {OUT.relative_to(ROOT)}/  (QR → {site['site_url']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
