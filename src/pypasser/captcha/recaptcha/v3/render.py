"""Resolve the current reCaptcha render version (``v``) from Google's api.js.

A stale render version in the anchor URL is a self-inflicted bot signal and it
also lands in the reload body (field 1). Chrome always renders with whatever
release ``api.js`` currently points at, so the version is fetched per solve.

Any failure (network, regex, unexpected body) returns ``None`` — callers fall
back to the version from the anchor URL. Results are cached per endpoint for
an hour so repeated solves stay fast.
"""

from __future__ import annotations

import re
import time
from collections import Counter
from typing import Optional

import httpx

API_JS_URL = "https://www.google.com/recaptcha/{api}.js"

_RELEASES_RE = re.compile(r"releases/([^/'\"\\)]+)/")
_CACHE_TTL = 3600.0
_cache: dict[str, tuple[float, str]] = {}


def _api_name(endpoint: str) -> str:
    return "api" if endpoint == "api2" else "enterprise"


def pick_release_version(js_text: str) -> Optional[str]:
    """Pick the current render version from api.js source.

    The script references its bundles as ``/recaptcha/releases/<version>/...``;
    the newest common release wins.
    """
    versions = _RELEASES_RE.findall(js_text)
    if not versions:
        return None
    return Counter(versions).most_common(1)[0][0]


def _store(endpoint: str, version: str) -> str:
    _cache[endpoint] = (time.monotonic() + _CACHE_TTL, version)
    return version


def latest_render_version(
    endpoint: str,
    client: Optional[httpx.Client] = None,
    timeout: float = 10,
) -> Optional[str]:
    """Fetch the current render version for ``endpoint`` ("api2"/"enterprise").

    ``client`` lets the caller reuse its own httpx client (proxy, mounts).
    Never raises — returns ``None`` on any failure.
    """
    cached = _cache.get(endpoint)
    if cached is not None and cached[0] > time.monotonic():
        return cached[1]
    try:
        if client is not None:
            response = client.get(API_JS_URL.format(api=_api_name(endpoint)), timeout=timeout)
        else:
            with httpx.Client() as temp:
                response = temp.get(API_JS_URL.format(api=_api_name(endpoint)), timeout=timeout)
        if response.status_code != 200:
            return None
        version = pick_release_version(response.text)
    except Exception:
        return None
    return _store(endpoint, version) if version else None


async def alatest_render_version(
    endpoint: str,
    client: Optional[httpx.AsyncClient] = None,
    timeout: float = 10,
) -> Optional[str]:
    """Async version of :func:`latest_render_version`."""
    cached = _cache.get(endpoint)
    if cached is not None and cached[0] > time.monotonic():
        return cached[1]
    try:
        if client is not None:
            response = await client.get(
                API_JS_URL.format(api=_api_name(endpoint)), timeout=timeout
            )
        else:
            async with httpx.AsyncClient() as temp:
                response = await temp.get(
                    API_JS_URL.format(api=_api_name(endpoint)), timeout=timeout
                )
        if response.status_code != 200:
            return None
        version = pick_release_version(response.text)
    except Exception:
        return None
    return _store(endpoint, version) if version else None


def clear_cache() -> None:
    """Drop cached versions (tests)."""
    _cache.clear()
