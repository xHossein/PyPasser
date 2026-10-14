"""Page-mode ARCaptcha solver.

Two situations, handled in order:

1. The page's own widget already ran (many sites auto-pass with a
   ``cookie``/``accept`` challenge) — the token is waiting in the hidden
   ``arcaptcha-token`` input, and reading it is the whole solve.
2. No token yet — the challenge is solved over HTTP (:mod:`solver`) and the
   token is written into the same input (best effort — the field is hidden,
   so a browser that refuses to fill it still gets the token back in the
   result), ready for the site's own form submission.

The token is the challenge id, submitted as the form field
``arcaptcha-token``.
"""

from __future__ import annotations

import asyncio
import time
from typing import TYPE_CHECKING, Any, Union

from pypasser.browsers import AsyncBrowserAdapter, BrowserAdapter, adetect, detect
from pypasser.captcha.arcaptcha.constants import TOKEN_INPUT_SELECTOR
from pypasser.captcha.arcaptcha.solver import ARCaptchaSolver
from pypasser.structs import SolverResult

if TYPE_CHECKING:  # pragma: no cover
    from playwright.async_api import Page as AsyncPage
    from playwright.sync_api import Page as SyncPage

_POLL_INTERVAL = 0.25


class PageARCaptchaSolver:
    """Sync page-mode ARCaptcha solver (Playwright page)."""

    def solve(
        self,
        page: "SyncPage | BrowserAdapter",
        site_key: str,
        domain: str,
        token_wait: Union[int, float] = 5,
        attempts: int = 3,
        **kwargs: Any,
    ) -> SolverResult:
        """Solve ARCaptcha on ``page`` and return the token.

        Parameters
        ----------
        page: Playwright sync page (or an adapter)
            A page already running the target site.
        site_key: str
            The site's ARCaptcha site key (the widget is identified by it).
        domain: str
            Domain the site key is registered for.
        token_wait: int or float
            Seconds to wait for the page's own widget to produce a token
            before falling back to the HTTP solver.
        attempts: int
            Challenge attempts for the HTTP fallback solver.
        kwargs:
            Forwarded to :class:`ARCaptchaSolver` (``proxy``, ``timeout``, ...).
        """
        adapter = page if isinstance(page, BrowserAdapter) else detect(page)

        token = self._read_token(adapter, token_wait)
        if token:
            return SolverResult(is_solved=True, response_token=token)

        token = ARCaptchaSolver(site_key, domain, **kwargs).solve(attempts=attempts)
        self._inject(adapter, token)
        return SolverResult(is_solved=True, response_token=token)

    def _read_token(self, adapter: BrowserAdapter, timeout: Union[int, float]) -> str | None:
        """Poll the hidden token input for the widget's own solve."""
        deadline = time.monotonic() + timeout
        while True:
            token = adapter.attr(TOKEN_INPUT_SELECTOR, "value", timeout=1)
            if token:
                return token
            if time.monotonic() >= deadline:
                return None
            time.sleep(_POLL_INTERVAL)

    def _inject(self, adapter: BrowserAdapter, token: str) -> None:
        """Best-effort: fill the token into the hidden input.

        The input is hidden, so a browser that rejects filling hidden fields
        leaves it empty — the caller still gets the token in the result and
        can submit it as the ``arcaptcha-token`` form field.
        """
        try:
            if adapter.exists(TOKEN_INPUT_SELECTOR):
                adapter.type(TOKEN_INPUT_SELECTOR, token, submit=False)
        except Exception:
            pass


class AsyncPageARCaptchaSolver:
    """Async page-mode ARCaptcha solver (async Playwright page)."""

    async def solve(
        self,
        page: "AsyncPage",
        site_key: str,
        domain: str,
        token_wait: Union[int, float] = 5,
        attempts: int = 3,
        **kwargs: Any,
    ) -> SolverResult:
        """Async version of :meth:`PageARCaptchaSolver.solve`."""
        from pypasser.captcha.arcaptcha.asolver import AsyncARCaptchaSolver

        adapter = (
            page if isinstance(page, AsyncBrowserAdapter) else adetect(page)
        )

        token = await self._read_token(adapter, token_wait)
        if token:
            return SolverResult(is_solved=True, response_token=token)

        token = await AsyncARCaptchaSolver(site_key, domain, **kwargs).solve(attempts=attempts)
        await self._inject(adapter, token)
        return SolverResult(is_solved=True, response_token=token)

    async def _read_token(
        self, adapter: "AsyncBrowserAdapter", timeout: Union[int, float]
    ) -> str | None:
        """Poll the hidden token input for the widget's own solve."""
        deadline = time.monotonic() + timeout
        while True:
            token = await adapter.attr(TOKEN_INPUT_SELECTOR, "value", timeout=1)
            if token:
                return token
            if time.monotonic() >= deadline:
                return None
            await asyncio.sleep(_POLL_INTERVAL)

    async def _inject(self, adapter: "AsyncBrowserAdapter", token: str) -> None:
        """Best-effort fill of the hidden token input (see the sync variant)."""
        try:
            if await adapter.exists(TOKEN_INPUT_SELECTOR):
                await adapter.type(TOKEN_INPUT_SELECTOR, token, submit=False)
        except Exception:
            pass


__all__ = ["PageARCaptchaSolver", "AsyncPageARCaptchaSolver"]
