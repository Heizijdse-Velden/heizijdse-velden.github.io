from __future__ import annotations

import os
import threading
from collections.abc import Iterator
from pathlib import Path

import pytest

from sitegen import CONTENT_DIR
from sitegen.build import build
from sitegen.content import Content, load_content
from sitegen.server import make_server


@pytest.fixture(scope="session")
def content() -> Content:
    return load_content(CONTENT_DIR)


@pytest.fixture(scope="session")
def site(content: Content, tmp_path_factory: pytest.TempPathFactory) -> Path:
    """The site, built once per test session."""
    out = tmp_path_factory.mktemp("site")
    build(content, out)
    return out


@pytest.fixture(scope="session")
def base_url(site: Path) -> Iterator[str]:
    """The built site served locally, with GitHub Pages' 404 behaviour."""
    server = make_server(site)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_address[1]}"
    server.shutdown()
    server.server_close()


CHROMIUM_HINT = "Chromium is not installed. Run once: uv run playwright install chromium"
_session = {"chromium_missing": False}


@pytest.fixture(scope="session")
def browser() -> Iterator[object]:
    """Headless Chromium. Skipped locally if not installed; required in CI (REQUIRE_E2E=1)."""
    sync_api = pytest.importorskip("playwright.sync_api")
    with sync_api.sync_playwright() as p:
        try:
            chromium = p.chromium.launch(executable_path=os.environ.get("CHROMIUM_PATH") or None)
        except sync_api.Error as exc:
            if os.environ.get("REQUIRE_E2E") or "Executable doesn't exist" not in str(exc):
                raise
            _session["chromium_missing"] = True
            pytest.skip(CHROMIUM_HINT)
        yield chromium
        chromium.close()


def pytest_terminal_summary(terminalreporter: pytest.TerminalReporter) -> None:
    """Skipped browser tests should be impossible to miss."""
    if _session["chromium_missing"]:
        terminalreporter.write_sep("=", "browser tests were skipped", yellow=True, bold=True)
        terminalreporter.write_line(CHROMIUM_HINT, yellow=True, bold=True)
