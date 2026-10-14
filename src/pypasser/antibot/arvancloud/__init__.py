"""ArvanCloud anti-bot bypass (browserless — cookie replay).

Two call styles mirror the reCaptcha solvers: an explicit URL sync solve, and
its async counterpart::

    from pypasser.antibot import arvancloud

    res = arvancloud.solve("https://example.ir/protected")
    res = await arvancloud.asolve("https://example.ir/protected")

Sites sit behind ArvanCloud with its challenge ("bot protection") switched on;
the bypass needs no browser. The result carries the cleared cookies plus the
User-Agent they are bound to (:class:`~pypasser.structs.SolverResult`), so the
same session can be replayed over plain HTTP — see
``examples/antibot/interstitial.py``.
"""

from __future__ import annotations

from typing import Optional, Union

from pypasser.antibot.arvancloud.aflow import AsyncArvanCloudBypass
from pypasser.antibot.arvancloud.flow import DEFAULT_UA, ArvanCloudBypass
from pypasser.structs import SolverResult

__all__ = ["solve", "asolve", "ArvanCloudBypass", "AsyncArvanCloudBypass"]


def solve(
    url: str,
    proxy: Optional[str] = None,
    timeout: Union[int, float] = 30,
    attempts: int = 3,
    user_agent: str = DEFAULT_UA,
) -> SolverResult:
    """Bypass the ArvanCloud challenge in front of ``url``.

    Parameters
    ----------
    url: str
        Any page of the protected site.
    proxy: str, optional
        Proxy URL — the clearance is tied to the exit IP.
    timeout: int or float
        Per-request timeout in seconds.
    attempts: int
        Challenge/answer round trips before giving up.
    user_agent: str
        User-Agent sent with the requests; the returned cookies are only
        valid for the same UA when replayed.
    """
    return ArvanCloudBypass(timeout=timeout, user_agent=user_agent).solve(
        url, proxy=proxy, attempts=attempts
    )


async def asolve(
    url: str,
    proxy: Optional[str] = None,
    timeout: Union[int, float] = 30,
    attempts: int = 3,
    user_agent: str = DEFAULT_UA,
) -> SolverResult:
    """Async version of :func:`solve`."""
    return await AsyncArvanCloudBypass(timeout=timeout, user_agent=user_agent).solve(
        url, proxy=proxy, attempts=attempts
    )
