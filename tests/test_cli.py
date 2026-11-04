"""The ``sitegen`` command and the local server."""

from __future__ import annotations

import os
import shutil
import subprocess
import threading
import urllib.error
import urllib.request
from pathlib import Path

import pytest

from sitegen import CONTENT_DIR
from sitegen.cli import main
from sitegen.server import make_server


def test_check_reports_ok(capsys: pytest.CaptureFixture[str]) -> None:
    main(["check"])
    assert "OK: 10 languages are complete." in capsys.readouterr().out


def test_build_writes_the_site(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    main(["build", "--out", str(tmp_path / "site")])
    assert (tmp_path / "site" / "nl" / "index.html").is_file()
    assert "Built 10 languages" in capsys.readouterr().out


def test_content_errors_stop_the_build_with_a_readable_message(tmp_path: Path) -> None:
    content = tmp_path / "content"
    shutil.copytree(CONTENT_DIR, content)
    (content / "lang" / "es.json").unlink()
    with pytest.raises(SystemExit, match=r"nothing was built\):\n  - content/lang/es\.json is missing"):
        main(["build", "--content", str(content), "--out", str(tmp_path / "out")])
    assert not (tmp_path / "out").exists()


def test_json_syntax_errors_are_readable(tmp_path: Path) -> None:
    content = tmp_path / "content"
    shutil.copytree(CONTENT_DIR, content)
    (content / "poster.json").write_text("{", encoding="utf-8")
    with pytest.raises(SystemExit, match=r"poster\.json, line 1, column 2"):
        main(["check", "--content", str(content)])


def test_warnings_go_to_stderr_but_do_not_fail(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    content = tmp_path / "content"
    shutil.copytree(CONTENT_DIR, content)
    site_json = content / "site.json"
    site_json.write_text(site_json.read_text().replace('"publisher": "Pieter Huycke"', '"publisher": ""'))
    main(["check", "--content", str(content)])
    assert "warning: site.json: 'publisher' (V.U.) is empty" in capsys.readouterr().err


def _get(url: str, method: str = "GET") -> tuple[int, bytes]:
    request = urllib.request.Request(url, method=method)
    try:
        with urllib.request.urlopen(request) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read()


def test_server_serves_files_and_the_custom_404(tmp_path: Path) -> None:
    (tmp_path / "index.html").write_text("home")
    server = make_server(tmp_path)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{server.server_address[1]}"
    try:
        assert _get(base + "/") == (200, b"home")
        assert _get(base + "/missing")[0] == 404  # no 404.html yet: the server's default page

        (tmp_path / "404.html").write_text("custom")
        assert _get(base + "/missing") == (404, b"custom")
        assert _get(base + "/missing", "HEAD") == (404, b"")
    finally:
        server.shutdown()
        server.server_close()


def _sitegen(*args: str, **env: str) -> subprocess.CompletedProcess[str]:
    """Run the installed ``sitegen`` command in a fresh process, like a maintainer would."""
    command = shutil.which("sitegen")
    assert command is not None
    return subprocess.run(  # noqa: S603 - fixed command, arguments from the test itself
        [command, *args], capture_output=True, text=True, env={**os.environ, **env}, check=False
    )


def test_poster_without_chromium_explains_how_to_install(tmp_path: Path) -> None:
    result = _sitegen(
        "poster",
        "--out",
        str(tmp_path / "site"),
        "--pdf",
        str(tmp_path / "a.pdf"),
        PLAYWRIGHT_BROWSERS_PATH=str(tmp_path / "no-browsers"),
    )
    assert result.returncode == 1
    assert "uv run playwright install chromium" in result.stderr
    assert not (tmp_path / "a.pdf").exists()


@pytest.mark.e2e
@pytest.mark.usefixtures("browser")  # skips when Chromium is missing
def test_poster_command_writes_the_pdf(tmp_path: Path) -> None:
    pdf = tmp_path / "outputs" / "affiche.pdf"
    result = _sitegen("poster", "--out", str(tmp_path / "site"), "--pdf", str(pdf))
    assert result.returncode == 0, result.stderr
    assert pdf.read_bytes().startswith(b"%PDF")
