"""Lemin cropped captcha (``cropped`` widget) solver.

The challenge is a jigsaw piece that has to be dragged onto the matching
silhouette in a photo. It is solved entirely over HTTP: fetch the scene, find
the slot with classic CV, submit a drag path."""

from __future__ import annotations

from typing import Union

from pypasser.captcha.lemin.asolver import AsyncLeminSolver
from pypasser.captcha.lemin.constants import DEFAULT_UA
from pypasser.captcha.lemin.solver import Challenge, LeminSolver
from pypasser.captcha.lemin.transport import DEFAULT_SCREEN
from pypasser.structs import SolverResult

__all__ = ["solve", "asolve", "Challenge", "LeminSolver", "AsyncLeminSolver"]


def solve(
    captcha_id: str,
    *,
    domain: str,
    proxy: Union[str, None] = None,
    timeout: Union[int, float] = 20,
    user_agent: str = DEFAULT_UA,
    screen: tuple[int, int] = DEFAULT_SCREEN,
    attempts: int = 3,
    jitter: float = 3.0,
) -> SolverResult:
    """Solve a Lemin cropped challenge.

    Parameters
    ----------
    captcha_id: str
        The target's captcha id, as ``CROPPED_<site>_<hash>``.
    domain: str
        Origin the widget runs on, e.g. ``"https://example.com"``. Lemin
        checks it against the captcha id's registration.
    proxy: str, optional
        Proxy URL, e.g. ``"socks5://user:pass@host:port"``.
    timeout: int or float
        Per-request timeout in seconds.
    user_agent: str
        User-Agent sent with the requests.
    screen: tuple of int
        Screen size reported to the image endpoint.
    attempts: int
        Fresh challenges to try before giving up. A rejected answer burns the
        challenge, so every attempt fetches a new one.
    jitter: float
        Random offset, in pixels, applied to each point of the drag path.
    """
    token, answer, challenge_id = LeminSolver(
        captcha_id,
        domain,
        proxy=proxy,
        timeout=timeout,
        user_agent=user_agent,
        screen=screen,
        jitter=jitter,
    ).solve(attempts=attempts)
    return SolverResult(
        is_solved=True,
        response_token={
            "pv_token": token,
            "answer": answer,
            "challenge_id": challenge_id,
        },
    )


async def asolve(
    captcha_id: str,
    *,
    domain: str,
    proxy: Union[str, None] = None,
    timeout: Union[int, float] = 20,
    user_agent: str = DEFAULT_UA,
    screen: tuple[int, int] = DEFAULT_SCREEN,
    attempts: int = 3,
    jitter: float = 3.0,
) -> SolverResult:
    """Async version of :func:`solve`."""
    token, answer, challenge_id = await AsyncLeminSolver(
        captcha_id,
        domain,
        proxy=proxy,
        timeout=timeout,
        user_agent=user_agent,
        screen=screen,
        jitter=jitter,
    ).solve(attempts=attempts)
    return SolverResult(
        is_solved=True,
        response_token={
            "pv_token": token,
            "answer": answer,
            "challenge_id": challenge_id,
        },
    )
