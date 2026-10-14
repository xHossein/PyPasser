"""Bowman fingerprint payload for ARCaptcha session creation."""

from __future__ import annotations

import random
import string
from datetime import datetime, timezone
from typing import Any


def rand32() -> str:
    """32-character lowercase alphanumeric id."""
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=32))


def build_bowman(
    site_key: str,
    domain: str,
    *,
    lang: str = "fa",
) -> dict[str, Any]:
    """Build a fresh bowman payload.

    Parameters
    ----------
    site_key: str
        The target's ARCaptcha site key.
    domain: str
        Domain the widget is embedded on (must be registered for the key).
    lang: str
        Content language.
    """
    now = datetime.now(timezone.utc)
    local = datetime.now().astimezone()
    bowman: dict[str, Any] = {
        "site_key": site_key,
        "domain": domain,
        "bowman_id": "s-" + rand32(),
        "system_time": now.isoformat(),
        "CR": "FAKE_CR",
        "fp": "fp-" + rand32(),
        "lang": lang,
        "last_seen_url": f"https://{domain}/",
        "timezone_cr": local.tzname() or "UTC",
    }
    return bowman
