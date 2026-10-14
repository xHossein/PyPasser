"""reCaptcha V3 solvers.

Two call styles::

    # HTTP mode from an anchor URL
    recaptcha.v3.solve("https://www.google.com/recaptcha/api2/anchor?ar=1&k=...&co=...")

    # Page mode: let the site's own JS produce the token, read it from the DOM
    recaptcha.v3.solve(page)

Both modes have an async counterpart: ``asolve``.
"""

from __future__ import annotations

from typing import Any, Optional, Union

from pypasser.captcha.recaptcha.v3.aflow import AsyncV3Solver
from pypasser.captcha.recaptcha.v3.flow import V3Solver
from pypasser.captcha.recaptcha.v3.pageflow import AsyncPageV3Solver, PageV3Solver
from pypasser.exceptions import InvalidAnchorURL
from pypasser.structs import SolverResult

__all__ = ["solve", "asolve", "V3Solver", "AsyncV3Solver"]


def _resolve_target(
    first: Any,
    anchor_url: Optional[str],
    page: Any,
) -> tuple[Optional[str], Any]:
    """Resolve the dispatch arguments into (anchor_url, page)."""
    if first is not None:
        if isinstance(first, str):
            anchor_url = first
        else:
            page = first

    if page is not None and anchor_url is not None:
        raise InvalidAnchorURL("Pass either a page or an anchor URL, not both.")

    if page is None and anchor_url is None:
        raise InvalidAnchorURL(
            "Provide an anchor URL or a page. Example: "
            "recaptcha.v3.solve('https://www.google.com/recaptcha/api2/anchor?ar=1&k=...')"
        )

    return anchor_url, page


def solve(
    first: Any = None,
    *,
    anchor_url: Optional[str] = None,
    page: Any = None,
    proxy: Optional[str] = None,
    timeout: Union[int, float] = 20,
) -> SolverResult:
    """Solve reCaptcha V3 and return a :class:`SolverResult`.

    Parameters
    ----------
    first: str or page, optional
        Positional target: an anchor URL (HTTP mode) or a browser page
        (page mode). Equivalent to the matching keyword.
    anchor_url: str, optional
        Full anchor URL copied from the browser's network tab, e.g.
        ``"https://www.google.com/recaptcha/api2/anchor?ar=1&k=SITE_KEY&co=..."``.
    page: page object, optional
        A page (Playwright sync) already
        running the target site.
    proxy: str, optional
        Proxy URL, e.g. ``"socks5://user:pass@host:port"`` (HTTP mode only).
    timeout: int or float
        Timeout in seconds (HTTP mode) or token wait (page mode).
    """
    anchor_url, page = _resolve_target(first, anchor_url, page)

    if page is not None:
        return PageV3Solver().solve(page, timeout=timeout)

    assert anchor_url is not None
    return V3Solver(anchor_url, proxy=proxy, timeout=timeout).solve()


async def asolve(
    first: Any = None,
    *,
    anchor_url: Optional[str] = None,
    page: Any = None,
    proxy: Optional[str] = None,
    timeout: Union[int, float] = 20,
) -> SolverResult:
    """Async version of :func:`solve` (HTTP mode and async page mode)."""
    anchor_url, page = _resolve_target(first, anchor_url, page)

    if page is not None:
        return await AsyncPageV3Solver().solve(page, timeout=timeout)

    assert anchor_url is not None
    return await AsyncV3Solver(anchor_url, proxy=proxy, timeout=timeout).solve()
