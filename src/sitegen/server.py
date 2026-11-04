"""Local static server that behaves like GitHub Pages for unknown URLs (serves /404.html)."""

from __future__ import annotations

import functools
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


class PagesRequestHandler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:  # noqa: A002 - signature from stdlib
        pass  # keep test and terminal output clean

    def send_error(self, code: int, message: str | None = None, explain: str | None = None) -> None:
        not_found_page = Path(self.directory) / "404.html"
        if code != HTTPStatus.NOT_FOUND or not not_found_page.is_file():
            super().send_error(code, message, explain)
            return
        body = not_found_page.read_bytes()
        self.send_response(HTTPStatus.NOT_FOUND)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)


def make_server(directory: Path, port: int = 0, host: str = "127.0.0.1") -> ThreadingHTTPServer:
    """Port 0 picks a free port; read it back from server.server_address[1]."""
    handler = functools.partial(PagesRequestHandler, directory=str(directory))
    return ThreadingHTTPServer((host, port), handler)
