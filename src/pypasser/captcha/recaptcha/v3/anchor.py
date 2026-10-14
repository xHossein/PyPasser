from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import parse_qs

from pypasser.exceptions import InvalidAnchorURL

ANCHOR_RE = re.compile(
    r"^https?://(?:www\.)?google\.com/recaptcha/(?P<endpoint>api2|enterprise)/anchor\?(?P<query>.*)$"
)


@dataclass(frozen=True)
class ParsedAnchor:
    """A parsed anchor URL."""

    endpoint: str
    params: dict[str, str]


def parse_anchor_url(anchor_url: str) -> ParsedAnchor:
    """Parse an anchor URL into endpoint + params.

    Raises
    ------
    InvalidAnchorURL
        If the URL is not a reCaptcha anchor URL.
    """
    if not isinstance(anchor_url, str):
        raise InvalidAnchorURL(f"anchor URL must be a string, got {type(anchor_url).__name__}")

    match = ANCHOR_RE.match(anchor_url.strip())
    if not match:
        raise InvalidAnchorURL(
            "Not a reCaptcha anchor URL. Expected "
            "https://www.google.com/recaptcha/{api2|enterprise}/anchor?ar=1&k=SITE_KEY&co=... "
            "(copy the full anchor URL from your browser's network tab)."
        )

    params = {
        k: v[0]
        for k, v in parse_qs(match.group("query"), keep_blank_values=True).items()
    }
    if "k" not in params or "co" not in params:
        raise InvalidAnchorURL(
            "Anchor URL is missing required parameters (k/co). "
            "Copy the full anchor URL from your browser's network tab."
        )

    return ParsedAnchor(endpoint=match.group("endpoint"), params=params)
