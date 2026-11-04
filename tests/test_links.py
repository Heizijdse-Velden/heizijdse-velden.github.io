"""External links still work. Needs internet: `uv run pytest -m external` (runs weekly in CI)."""

from __future__ import annotations

import time
import urllib.error
import urllib.request

import pytest

from sitegen import CONTENT_DIR
from sitegen.content import all_links, load_content

USER_AGENT = "Mozilla/5.0 (compatible; heizijdse-velden-linkcheck/1.0)"


def _unique_links() -> dict[str, str]:
    """url -> first name it appears under, so every URL is checked once."""
    unique: dict[str, str] = {}
    for name, url in all_links(load_content(CONTENT_DIR).site):
        unique.setdefault(url, name)
    return unique


def _status(url: str, method: str) -> int:
    request = urllib.request.Request(url, method=method, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:  # follows redirects
            return response.status
    except urllib.error.HTTPError as exc:
        return exc.code
    except (urllib.error.URLError, TimeoutError):
        return 599  # unreachable: DNS failure, refused connection, timeout


LINKS = _unique_links()


@pytest.mark.external
@pytest.mark.parametrize("url", list(LINKS), ids=list(LINKS.values()))
def test_external_link_works(url: str) -> None:
    status = 0
    for attempt in range(3):
        status = _status(url, "HEAD")
        if status in (403, 405, 501):  # some servers refuse HEAD; ask for the page instead
            status = _status(url, "GET")
        if status < 400 or status == 404:
            break  # 404 won't fix itself by retrying
        time.sleep(2 * (attempt + 1))
    assert status < 400, f"{url} answered HTTP {status}"
