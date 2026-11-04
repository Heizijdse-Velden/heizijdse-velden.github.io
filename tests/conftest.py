"""Shared fixtures: the content, the built site, a local server, and a headless browser."""

from __future__ import annotations

import os
import threading
from collections.abc import Iterator
from pathlib import Path

import pytest
from playwright.sync_api import Browser, Error, sync_playwright

from sitegen import CONTENT_DIR
from sitegen.build import build
from sitegen.content import Content, load_content
from sitegen.poster import INSTALL_HINT
from sitegen.server import make_server

_session = {"chromium_missing": False}


@pytest.fixture(scope="session")
def content() -> Content:
    """Load the real content of the site."""
    return load_content(CONTENT_DIR)


@pytest.fixture(scope="session")
def site(content: Content, tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Build the site once per test session."""
    out = tmp_path_factory.mktemp("site")
    build(content, out)
    return out


@pytest.fixture(scope="session")
def base_url(site: Path) -> Iterator[str]:
    """Serve the built site locally, with GitHub Pages' 404 behaviour."""
    server = make_server(site)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_address[1]}"
    server.shutdown()
    server.server_close()


@pytest.fixture(scope="session")
def browser() -> Iterator[Browser]:
    """Start headless Chromium. Skipped locally if it isn't installed; required in CI (REQUIRE_E2E=1)."""
    with sync_playwright() as playwright:
        try:
            chromium = playwright.chromium.launch()
        except Error as exc:
            if os.environ.get("REQUIRE_E2E") or "Executable doesn't exist" not in str(exc):
                raise
            _session["chromium_missing"] = True
            pytest.skip(INSTALL_HINT)
        yield chromium
        chromium.close()


def pytest_terminal_summary(terminalreporter: pytest.TerminalReporter) -> None:
    """Make skipped browser tests impossible to miss."""
    if _session["chromium_missing"]:
        terminalreporter.write_sep("=", "browser tests were skipped", yellow=True, bold=True)
        terminalreporter.write_line(INSTALL_HINT, yellow=True, bold=True)
