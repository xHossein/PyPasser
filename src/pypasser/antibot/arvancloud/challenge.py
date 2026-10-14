"""Detection and decoding of the ArvanCloud challenge page.

An ArvanCloud-protected site serves a JS-only interstitial at first request:
a page whose ``values()`` function hides the ``__arcsjs`` / ``__arcsjsc``
cookie values in JSFuck, and whose ``DOMContentLoaded`` handler writes them
as cookies and reloads. Replaying those two cookies on the next request
passes the challenge — the rest of the page is irrelevant.
"""

from __future__ import annotations

import re
from urllib.parse import urlparse

from pypasser.antibot.arvancloud.decoder import extract_values

CHALLENGE_MARKERS = ("function values()", "__arcsjs")
_SCRIPT_RE = re.compile(r"<script[^>]*>\s*function values\(\).*?</script>", re.S)

COOKIE_ARCSJS = "__arcsjs"
COOKIE_ARCSJSC = "__arcsjsc"


def is_challenge(html: str) -> bool:
    """Whether a response body is the ArvanCloud challenge page."""
    return all(marker in html for marker in CHALLENGE_MARKERS)


def cookie_domain(url: str) -> str:
    """The cookie domain the challenge writes: the registrable domain.

    ArvanCloud sets ``Domain=<last two labels>`` on the interstitial's own
    copy (``esale.ikco.ir`` -> ``ikco.ir``); a shorter host is used as-is.
    """
    host = (urlparse(url).hostname or "").lower()
    if not host:
        from pypasser.exceptions import ArvanChallengeError

        raise ArvanChallengeError(f"cannot determine a host from URL: {url!r}")
    parts = host.split(".")
    return ".".join(parts[-2:]) if len(parts) > 2 else host


def challenge_cookies(html: str) -> dict[str, str]:
    """Decode the challenge page into the two clearance cookies.

    Raises
    ------
    ArvanChallengeError
        If the ``values()`` function or its payloads cannot be decoded.
    """
    from pypasser.exceptions import ArvanChallengeError

    match = _SCRIPT_RE.search(html)
    if not match:
        raise ArvanChallengeError("challenge page has no values() script block")
    try:
        value_v1, value = extract_values(match.group(0))
    except Exception as exc:
        raise ArvanChallengeError(f"cannot decode ArvanCloud challenge: {exc}") from exc
    if not value_v1 or not value:
        raise ArvanChallengeError("decoded challenge cookies are empty")
    return {COOKIE_ARCSJS: value_v1, COOKIE_ARCSJSC: value}
