"""Command line interface: `uv run sitegen {check,build,serve,poster}`."""

from __future__ import annotations

import argparse
import contextlib
import sys
from collections.abc import Callable
from pathlib import Path

from sitegen import CONTENT_DIR, OUTPUT_DIR, PROJECT_ROOT
from sitegen.build import build
from sitegen.content import Content, load_content, validate
from sitegen.server import make_server


def _load_and_validate(content_dir: Path) -> Content:
    content = load_content(content_dir)
    errors, warnings = validate(content)
    for warning in warnings:
        print(f"warning: {warning}", file=sys.stderr)
    if errors:
        print("Content errors (nothing was built):", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        raise SystemExit(1)
    return content


def cmd_check(args: argparse.Namespace) -> None:
    content = _load_and_validate(args.content)
    print(f"OK: {len(content.langs)} languages are complete.")


def cmd_build(args: argparse.Namespace) -> None:
    content = _load_and_validate(args.content)
    build(content, args.out)
    print(f"Built {len(content.langs)} languages into {args.out} (QR code -> {content.site['site_url']})")


def cmd_serve(args: argparse.Namespace) -> None:
    cmd_build(args)
    with make_server(args.out, args.port) as server:
        print(f"Serving on http://localhost:{args.port}  (Ctrl+C to stop)")
        with contextlib.suppress(KeyboardInterrupt):
            server.serve_forever()


def cmd_poster(args: argparse.Namespace) -> None:
    from sitegen.poster import render_pdf

    cmd_build(args)
    render_pdf(args.out / "affiche" / "index.html", args.pdf)
    print(f"Poster written to {args.pdf}")


Handler = Callable[[argparse.Namespace], None]


def main(argv: list[str] | None = None) -> None:
    paths = argparse.ArgumentParser(add_help=False)
    paths.add_argument("--content", type=Path, default=CONTENT_DIR, help="content directory")
    paths.add_argument("--out", type=Path, default=OUTPUT_DIR, help="output directory")

    parser = argparse.ArgumentParser(prog="sitegen", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    def command(name: str, func: Handler, summary: str) -> argparse.ArgumentParser:
        p = sub.add_parser(name, help=summary, parents=[paths])
        p.set_defaults(func=func)
        return p

    command("check", cmd_check, "validate the content files")
    command("build", cmd_build, "build the site into _site/")
    serve = command("serve", cmd_serve, "build and serve the site locally")
    serve.add_argument("--port", type=int, default=8000)
    poster = command("poster", cmd_poster, "render the A4 poster to PDF (needs Chromium, see README)")
    poster.add_argument("--pdf", type=Path, default=PROJECT_ROOT / "affiche.pdf")

    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
