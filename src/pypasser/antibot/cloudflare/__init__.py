"""Cloudflare interstitial bypass (browser automation — cookie replay).

Clears the full-page Cloudflare challenge ("Just a moment...") in the current
browser tab and returns the session artifacts::

    from pypasser.antibot import cloudflare

    res = cloudflare.solve(playwright_page)     # sync
    res = await cloudflare.asolve(page)         # async Playwright

Cloudflare gates the whole site behind the interstitial — nothing else loads
until the challenge passes — and the challenge itself is a Turnstile widget
(the iframe from ``challenges.cloudflare.com``). On passage Cloudflare issues
the ``cf_clearance`` cookie; the result carries it (plus the ``user_agent`` it
is bound to), so a plain HTTP client can replay the cleared session from the
same IP::

    import httpx

    headers = {"User-Agent": result.user_agent} if result.user_agent else {}
    with httpx.Client(cookies=result.cookies, headers=headers, timeout=30) as client:
        html = client.get("https://example.com/protected").text

See ``examples/cloudflare/interstitial.py`` for a full steamdb.info example.
Driving it with **patchright** (a stealth Playwright fork) in a **headed**
browser is strongly recommended: vanilla Playwright gets scored as automation
and Cloudflare never renders the challenge for it, and the interstitial does
not clear headless either (live-measured — headless fails the wall even with
stealth patches). 

The embedded Turnstile *widget* (a checkbox inside a host page) is a captcha,
solved by :mod:`pypasser.captcha.turnstile` — this module is for the wall in
front of the site.
"""

from __future__ import annotations

from typing import Any, Union

from pypasser.antibot.cloudflare.aflow import AsyncCloudflareBypass
from pypasser.antibot.cloudflare.flow import DEFAULT_TIMEOUT, CloudflareBypass
from pypasser.structs import SolverResult

__all__ = ["solve", "asolve", "CloudflareBypass", "AsyncCloudflareBypass"]


def solve(
    page: Any,
    backend: str = "auto",
    attempts: int = 3,
    timeout: Union[int, float] = DEFAULT_TIMEOUT,
) -> SolverResult:
    """Clear the Cloudflare interstitial in the current browser tab.

    Parameters
    ----------
    page: page object
        A Playwright sync page (or stealth fork such as Patchright / Camoufox)
        sitting on the Cloudflare challenge page.
    backend: str
        ``"auto"`` (detect from object), ``"playwright"`` or ``"patchright"``.
    attempts: int
        Maximum checkbox-click attempts (Cloudflare re-renders the widget
        while the challenge runs, so a click can land on a stale node).
    timeout: int or float
        How long to keep polling for the widget / clearance, in seconds.
        Interstitials are slower than widgets — the default is generous.
    """
    return CloudflareBypass(attempts=attempts, timeout=timeout).solve(page, backend=backend)


async def asolve(
    page: Any,
    backend: str = "auto",
    attempts: int = 3,
    timeout: Union[int, float] = DEFAULT_TIMEOUT,
) -> SolverResult:
    """Async version of :func:`solve` (async Playwright pages only)."""
    return await AsyncCloudflareBypass(attempts=attempts, timeout=timeout).solve(
        page, backend=backend
    )
