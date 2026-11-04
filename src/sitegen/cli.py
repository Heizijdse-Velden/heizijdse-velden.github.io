"""Command line interface: ``uv run sitegen {check,build,serve,poster}``."""

from __future__ import annotations

import argparse
import contextlib
import sys
from collections.abc import Callable, Sequence
from pathlib import Path

from sitegen import CONTENT_DIR, OUTPUT_DIR, PROJECT_ROOT
from sitegen.build import build
from sitegen.content import Content, ContentError, load_content, validate
from sitegen.server import make_server

Command = Callable[[argparse.Namespace], None]


def _load_and_validate(content_dir: Path) -> Content:
    try:
        content = load_content(content_dir)
    except ContentError as exc:
        sys.exit(f"Content error (nothing was built):\n  - {exc}")
    errors, warnings = validate(content)
    for warning in warnings:
        print(f"warning: {warning}", file=sys.stderr)
    if errors:
        sys.exit("Content errors (nothing was built):\n" + "\n".join(f"  - {error}" for error in errors))
    return content


def cmd_check(args: argparse.Namespace) -> None:
    """Validate the content files."""
    content = _load_and_validate(args.content)
    print(f"OK: {len(content.langs)} languages are complete.")


def cmd_build(args: argparse.Namespace) -> None:
    """Build the site."""
    content = _load_and_validate(args.content)
    build(content, args.out)
    print(f"Built {len(content.langs)} languages into {args.out} (QR code -> {content.site['site_url']})")


def cmd_serve(args: argparse.Namespace) -> None:  # pragma: no cover - blocks until Ctrl+C
    """Build the site and serve it locally."""
    cmd_build(args)
    with make_server(args.out, args.port) as server:
        print(f"Serving on http://localhost:{args.port}  (Ctrl+C to stop)")
        with contextlib.suppress(KeyboardInterrupt):
            server.serve_forever()


def cmd_poster(args: argparse.Namespace) -> None:
    """Build the site and print the poster to PDF."""
    from sitegen.poster import render_pdf  # Playwright loads slowly; only the poster needs it.

    cmd_build(args)
    render_pdf(args.out / "affiche" / "index.html", args.pdf)
    print(f"Poster written to {args.pdf}")


def main(argv: Sequence[str] | None = None) -> None:
    """Run the ``sitegen`` command."""
    content_arg = argparse.ArgumentParser(add_help=False)
    content_arg.add_argument("--content", type=Path, default=CONTENT_DIR, help="content directory")
    out_arg = argparse.ArgumentParser(add_help=False)
    out_arg.add_argument("--out", type=Path, default=OUTPUT_DIR, help="output directory")

    parser = argparse.ArgumentParser(prog="sitegen", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    def command(name: str, func: Command, *parents: argparse.ArgumentParser) -> argparse.ArgumentParser:
        p = sub.add_parser(name, help=func.__doc__, parents=[content_arg, *parents])
        p.set_defaults(func=func)
        return p

    command("check", cmd_check)
    command("build", cmd_build, out_arg)
    command("serve", cmd_serve, out_arg).add_argument("--port", type=int, default=8000)
    command("poster", cmd_poster, out_arg).add_argument(
        "--pdf", type=Path, default=PROJECT_ROOT / "outputs" / "affiche.pdf", help="where to write the PDF"
    )

    args = parser.parse_args(argv)
    args.func(args)
