"""reCaptcha V2 solvers (audio challenge).

Usage::

    import pypasser.recaptcha as recaptcha
    res = recaptcha.v2.solve(page)                   # Playwright page, auto-detected
    res = recaptcha.v2.solve(page, backend='patchright')
    res = await recaptcha.v2.asolve(page)            # async Playwright page

Requires the audio dependencies::

    pip install PyPasser[speech]
"""

from __future__ import annotations

from typing import Any

from pypasser.captcha.recaptcha.v2.aflow import AsyncV2Solver
from pypasser.captcha.recaptcha.v2.flow import V2Solver
from pypasser.structs import SolverResult

__all__ = ["solve", "asolve", "V2Solver", "AsyncV2Solver"]


def solve(
    page: Any,
    backend: str = "auto",
    play: bool = True,
    attempts: int = 3,
    timeout: float = 10,
) -> SolverResult:
    """Solve the reCaptcha V2 challenge in the current browser tab.

    Parameters
    ----------
    page: page object
        A Playwright sync page positioned on a page
        with a reCaptcha V2 checkbox.
    backend: str
        ``"auto"`` (detect from object), ``"playwright"``, or ``"patchright"``
        (stealth Playwright fork).
    play: bool
        Click the audio play button (plays the audio aloud).
    attempts: int
        Maximum number of transcription attempts.
    timeout: float
        Per-step element wait timeout in seconds.
    """
    from pypasser.browsers import get_adapter

    adapter = get_adapter(backend, page)
    return V2Solver(play=play, attempts=attempts, timeout=timeout).solve(adapter)


async def asolve(
    page: Any,
    backend: str = "auto",
    play: bool = True,
    attempts: int = 3,
    timeout: float = 10,
) -> SolverResult:
    """Async version of :func:`solve` (async Playwright pages only)."""
    from pypasser.browsers import aget_adapter

    adapter = aget_adapter(backend, page)
    return await AsyncV2Solver(play=play, attempts=attempts, timeout=timeout).solve(adapter)
