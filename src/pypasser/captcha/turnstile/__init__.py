"""Cloudflare Turnstile captcha solver.

Usage::

    from pypasser.captcha import turnstile

    res = turnstile.solve(playwright_page)      # sync
    res = await turnstile.asolve(page)          # async Playwright

Solves both shapes of the widget:

- a **managed widget** embedded in a page (``.cf-turnstile`` container), and
- a **full-page interstitial** ("Checking your browser..." / "Just a
  moment...") where the Turnstile widget is Cloudflare's own challenge and the
  host page holds the hidden response input.

The solver waits for the widget iframe (served from
``challenges.cloudflare.com``), clicks the "Verify you are human" checkbox
inside it, and polls the hidden response input for the token — a non-empty
value is only written once the challenge fully passes.
"""

from __future__ import annotations

from typing import Any

from pypasser.captcha.turnstile.aflow import AsyncTurnstileSolver
from pypasser.captcha.turnstile.flow import TurnstileSolver
from pypasser.structs import SolverResult

__all__ = ["solve", "asolve", "TurnstileSolver", "AsyncTurnstileSolver"]


def solve(
    page: Any,
    backend: str = "auto",
    attempts: int = 3,
    timeout: float = 30,
) -> SolverResult:
    """Solve the Cloudflare Turnstile challenge in the current browser tab.

    Parameters
    ----------
    page: page object
        A Playwright sync page (or stealth fork such as Patchright / Camoufox)
        on a page with a Turnstile widget or a Turnstile challenge page.
    backend: str
        ``"auto"`` (detect from object), ``"playwright"`` or ``"patchright"``.
    attempts: int
        Maximum checkbox-click attempts (Cloudflare re-renders the widget
        while the challenge is running, so a click can land on a stale node).
    timeout: float
        How long to keep polling for the widget / token, in seconds.
    """
    from pypasser.browsers import get_adapter

    adapter = get_adapter(backend, page)
    return TurnstileSolver(attempts=attempts, timeout=timeout).solve(adapter)


async def asolve(
    page: Any,
    backend: str = "auto",
    attempts: int = 3,
    timeout: float = 30,
) -> SolverResult:
    """Async version of :func:`solve` (async Playwright pages only)."""
    from pypasser.browsers import aget_adapter

    adapter = aget_adapter(backend, page)
    return await AsyncTurnstileSolver(attempts=attempts, timeout=timeout).solve(adapter)
