"""External links still work. Needs internet: `uv run pytest -m external` (runs weekly in CI).

The check mimics a browser as far as it matters for "does the link work for a visitor":
a server with an incomplete certificate chain or legacy TLS renegotiation still opens in every
browser, so that passes with a warning. Real problems (expired certificate, wrong hostname,
HTTP errors, unreachable host) fail, and the failure message says why.
"""

from __future__ import annotations

import ssl
import time
import urllib.error
import urllib.request
import warnings
from dataclasses import dataclass

import pytest

from sitegen import CONTENT_DIR
from sitegen.content import all_links, load_content

USER_AGENT = "Mozilla/5.0 (compatible; heizijdse-velden-linkcheck/1.0)"
HEADERS = {"User-Agent": USER_AGENT, "Accept": "text/html,*/*;q=0.8", "Accept-Language": "nl-BE,nl;q=0.9"}
UNREACHABLE = 599

# OpenSSL verify codes for a chain the server sent incompletely (browsers fetch the missing part).
INCOMPLETE_CHAIN = {20, 21}  # unable to get local issuer certificate / unable to verify first certificate


@dataclass
class Result:
    status: int
    error: BaseException | None = None

    @property
    def ok(self) -> bool:
        return self.status < 400

    def __str__(self) -> str:
        return f"HTTP {self.status}" if self.error is None else f"{self.status}: {self.error!r}"


def _fetch(url: str, method: str, context: ssl.SSLContext | None = None) -> Result:
    request = urllib.request.Request(url, method=method, headers=HEADERS)
    try:
        with urllib.request.urlopen(request, timeout=20, context=context) as response:  # follows redirects
            return Result(response.status)
    except urllib.error.HTTPError as exc:
        return Result(exc.code, exc)
    except urllib.error.URLError as exc:
        return Result(UNREACHABLE, exc.reason if isinstance(exc.reason, BaseException) else exc)
    except (TimeoutError, ConnectionError, ssl.SSLError) as exc:
        return Result(UNREACHABLE, exc)


def browser_tolerated_tls_problem(error: BaseException | None) -> str | None:
    """Name the TLS quirk if browsers would still open the page, else None."""
    if isinstance(error, ssl.SSLCertVerificationError) and error.verify_code in INCOMPLETE_CHAIN:
        return "incomplete certificate chain"
    if isinstance(error, ssl.SSLError) and "UNSAFE_LEGACY_RENEGOTIATION" in str(error):
        return "legacy TLS renegotiation"
    return None


def _lenient_context() -> ssl.SSLContext:
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    context.options |= getattr(ssl, "OP_LEGACY_SERVER_CONNECT", 0x4)
    return context


def check_link(url: str, attempts: int = 3) -> Result:
    result = Result(0)
    for attempt in range(attempts):
        result = _fetch(url, "HEAD")
        if not result.ok:  # some servers refuse HEAD or drop it; ask for the page like a browser does
            result = _fetch(url, "GET")
        quirk = browser_tolerated_tls_problem(result.error)
        if quirk:
            lenient = _fetch(url, "GET", _lenient_context())
            if lenient.ok:
                warnings.warn(f"{url} works in browsers, but its server has an {quirk}", stacklevel=2)
            return lenient
        if result.ok or result.status == 404:  # a 404 won't fix itself by retrying
            return result
        time.sleep(2 * (attempt + 1))
    return result


def _unique_links() -> dict[str, str]:
    """Url -> first name it appears under, so every URL is checked once."""
    unique: dict[str, str] = {}
    for name, url in all_links(load_content(CONTENT_DIR).site):
        unique.setdefault(url, name)
    return unique


LINKS = _unique_links()


@pytest.mark.external
@pytest.mark.parametrize("url", list(LINKS), ids=list(LINKS.values()))
def test_external_link_works(url: str) -> None:
    result = check_link(url)
    assert result.ok, f"{url} -> {result}"


def _verify_error(code: int) -> ssl.SSLCertVerificationError:
    error = ssl.SSLCertVerificationError(1, "certificate verify failed")
    error.verify_code = code
    return error


@pytest.mark.parametrize(
    ("error", "tolerated"),
    [
        (_verify_error(20), True),  # incomplete chain: browsers repair this
        (_verify_error(10), False),  # expired certificate: browsers warn too
        (_verify_error(62), False),  # hostname mismatch
        (ssl.SSLError(1, "[SSL: UNSAFE_LEGACY_RENEGOTIATION_DISABLED] unsafe legacy renegotiation"), True),
        (ConnectionResetError(54, "Connection reset by peer"), False),
        (None, False),
    ],
)
def test_only_browser_tolerated_tls_problems_are_accepted(
    error: BaseException | None, tolerated: bool
) -> None:
    assert (browser_tolerated_tls_problem(error) is not None) is tolerated
