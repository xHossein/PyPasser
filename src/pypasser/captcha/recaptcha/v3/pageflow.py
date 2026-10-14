"""Page-mode solvers: let the site's own JavaScript produce a reCaptcha V3 token,
then read it from the page DOM.
"""

from __future__ import annotations

import asyncio
import time
from typing import TYPE_CHECKING, Union

from pypasser.browsers import BrowserAdapter, adetect, detect
from pypasser.exceptions import RecaptchaResponseNotFound
from pypasser.structs import SolverResult

if TYPE_CHECKING:  # pragma: no cover
    from playwright.async_api import Page as AsyncPage
    from playwright.sync_api import Page as SyncPage

_TOKEN_SELECTOR = "#g-recaptcha-response"
_POLL_INTERVAL = 0.25


class PageV3Solver:
    """Sync page-mode reCaptcha V3 bypass (Playwright page)."""

    def solve(
        self,
        page: "SyncPage | BrowserAdapter",
        timeout: Union[int, float] = 20,
    ) -> SolverResult:
        adapter = page if isinstance(page, BrowserAdapter) else detect(page)
        elapsed = 0.0
        while elapsed < timeout:
            token = adapter.attr(_TOKEN_SELECTOR, "value", timeout=1)
            if token:
                return SolverResult(is_solved=True, response_token=token)
            time.sleep(_POLL_INTERVAL)
            elapsed += _POLL_INTERVAL
        raise RecaptchaResponseNotFound(
            f"No token found in {_TOKEN_SELECTOR} within {timeout}s. "
            "Make sure the site ran reCaptcha before calling solve(page)."
        )


class AsyncPageV3Solver:
    """Async page-mode reCaptcha V3 bypass (async Playwright page)."""

    async def solve(self, page: "AsyncPage", timeout: Union[int, float] = 20) -> SolverResult:
        adapter = adetect(page)
        elapsed = 0.0
        while elapsed < timeout:
            token = await adapter.attr(_TOKEN_SELECTOR, "value", timeout=1)
            if token:
                return SolverResult(is_solved=True, response_token=token)
            await asyncio.sleep(_POLL_INTERVAL)
            elapsed += _POLL_INTERVAL
        raise RecaptchaResponseNotFound(
            f"No token found in {_TOKEN_SELECTOR} within {timeout}s. "
            "Make sure the site ran reCaptcha before calling solve(page)."
        )
