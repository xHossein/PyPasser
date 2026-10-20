"""ARCaptcha (arcaptcha.ir) solvers.

Two call styles, picked automatically from the arguments::

    # HTTP mode: solve a challenge by site key, get the token back
    token = arcaptcha.solve("SITE_KEY", domain="example.ir")

    # Page mode: read (or produce + inject) the token on a live page
    res = arcaptcha.solve(page, site_key="SITE_KEY", domain="example.ir")

Both modes have an async counterpart: ``asolve``. The token is the challenge
id; the site submits it as the ``arcaptcha-token`` form field.
"""

from __future__ import annotations

from typing import Any, Optional, Union

from pypasser.captcha.arcaptcha.pageflow import (
    AsyncPageARCaptchaSolver,
    PageARCaptchaSolver,
)
from pypasser.captcha.arcaptcha.solver import ARCaptchaSolver
from pypasser.exceptions import ARCaptchaError
from pypasser.structs import SolverResult

__all__ = ["solve", "asolve", "ARCaptchaSolver"]


def _resolve_target(
    first: Any,
    site_key: Optional[str],
    page: Any,
) -> tuple[Optional[str], Any]:
    """Resolve the dispatch arguments into (site_key, page)."""
    if first is not None:
        if isinstance(first, str):
            site_key = first
        else:
            page = first
    return site_key, page


def solve(
    first: Any = None,
    *,
    site_key: Optional[str] = None,
    domain: Optional[str] = None,
    page: Any = None,
    proxy: Optional[str] = None,
    timeout: Union[int, float] = 20,
    lang: str = "fa",
    voice_model: Union[str, None] = None,
    attempts: int = 3,
    token_wait: Union[int, float] = 5,
) -> SolverResult:
    """Solve an ARCaptcha challenge and return a :class:`SolverResult`.

    Parameters
    ----------
    first: str or page, optional
        Positional target: a site key (HTTP mode) or a browser page
        (page mode). Equivalent to the matching keyword.
    site_key: str, optional
        The target's ARCaptcha site key.
    domain: str, optional
        Domain the widget is embedded on (must be registered for the key).
    page: page object, optional
        A Playwright sync page already running the target site.
    proxy: str, optional
        Proxy URL, e.g. ``"socks5://user:pass@host:port"``.
    timeout: int or float
        Per-request timeout in seconds (HTTP mode).
    lang: str
        Content language sent with the requests.
    voice_model: str, optional
        vosk model name for voice challenges (defaults to the big Persian
        model, downloaded on first use).
    attempts: int
        Challenge attempts before giving up (HTTP mode).
    token_wait: int or float
        Seconds to wait for the page's own widget token before falling back
        to the HTTP solver (page mode).
    """
    site_key, page = _resolve_target(first, site_key, page)

    if page is not None:
        if not site_key or not domain:
            raise ARCaptchaError(
                "Page mode needs the site key and domain of the widget. Example: "
                "arcaptcha.solve(page, site_key='KEY', domain='example.ir')"
            )
        return PageARCaptchaSolver().solve(
            page,
            site_key,
            domain,
            token_wait=token_wait,
            proxy=proxy,
            timeout=timeout,
            lang=lang,
            voice_model=voice_model,
            attempts=attempts,
        )

    if not site_key or not domain:
        raise ARCaptchaError(
            "Provide a site key and its domain. Example: "
            "arcaptcha.solve('SITE_KEY', domain='example.ir')"
        )
    token = ARCaptchaSolver(
        site_key,
        domain,
        proxy=proxy,
        timeout=timeout,
        lang=lang,
        voice_model=voice_model,
    ).solve(attempts=attempts)
    return SolverResult(is_solved=True, response_token=token)


async def asolve(
    first: Any = None,
    *,
    site_key: Optional[str] = None,
    domain: Optional[str] = None,
    page: Any = None,
    proxy: Optional[str] = None,
    timeout: Union[int, float] = 20,
    lang: str = "fa",
    voice_model: Union[str, None] = None,
    attempts: int = 3,
    token_wait: Union[int, float] = 5,
) -> SolverResult:
    """Async version of :func:`solve` (HTTP mode and async page mode)."""
    from pypasser.captcha.arcaptcha.asolver import AsyncARCaptchaSolver

    site_key, page = _resolve_target(first, site_key, page)

    if page is not None:
        if not site_key or not domain:
            raise ARCaptchaError(
                "Page mode needs the site key and domain of the widget. Example: "
                "arcaptcha.asolve(page, site_key='KEY', domain='example.ir')"
            )
        return await AsyncPageARCaptchaSolver().solve(
            page,
            site_key,
            domain,
            token_wait=token_wait,
            proxy=proxy,
            timeout=timeout,
            lang=lang,
            voice_model=voice_model,
            attempts=attempts,
        )

    if not site_key or not domain:
        raise ARCaptchaError(
            "Provide a site key and its domain. Example: "
            "arcaptcha.solve('SITE_KEY', domain='example.ir')"
        )
    token = await AsyncARCaptchaSolver(
        site_key,
        domain,
        proxy=proxy,
        timeout=timeout,
        lang=lang,
        voice_model=voice_model,
    ).solve(attempts=attempts)
    return SolverResult(is_solved=True, response_token=token)
