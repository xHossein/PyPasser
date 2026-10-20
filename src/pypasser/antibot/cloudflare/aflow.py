"""Asynchronous Cloudflare interstitial clearance flow."""

from __future__ import annotations

from typing import Any

from pypasser.antibot.cloudflare.flow import (
    CHALLENGE_PAGE_MARKERS,
    DEFAULT_TIMEOUT,
    WIDGET_FRAME_SELECTORS,
    require_clearance,
)
from pypasser.browsers.session import asession_result
from pypasser.structs import SolverResult


async def _wall_present(adapter: Any) -> bool:
    """Whether the page currently shows the Cloudflare wall (async variant)."""
    try:
        source = (await adapter.page_source() or "").lower()
    except Exception:
        source = ""
    if any(marker in source for marker in CHALLENGE_PAGE_MARKERS):
        return True
    for selector in WIDGET_FRAME_SELECTORS:
        try:
            if await adapter.exists(selector):
                return True
        except Exception:
            continue
    return False


class AsyncCloudflareBypass:
    """Asynchronous Cloudflare interstitial bypass (async Playwright pages)."""

    def __init__(self, attempts: int = 3, timeout: float = DEFAULT_TIMEOUT) -> None:
        self.attempts = attempts
        self.timeout = timeout

    async def solve(self, page: Any, backend: str = "auto") -> SolverResult:
        from pypasser.browsers import aget_adapter
        from pypasser.captcha.turnstile.aflow import AsyncTurnstileSolver

        adapter = aget_adapter(backend, page)

        if not await _wall_present(adapter):
            return await asession_result(adapter)

        solver = AsyncTurnstileSolver(attempts=self.attempts, timeout=self.timeout)
        result = await solver.solve(adapter)
        if result.is_solved:
            require_clearance(result)
            return result

        if not await _wall_present(adapter):
            return await asession_result(adapter)
        return result
