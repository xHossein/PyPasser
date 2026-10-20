"""Asynchronous Cloudflare Turnstile solve flow."""

from __future__ import annotations

import asyncio
import time
from typing import TYPE_CHECKING, Optional

from pypasser.browsers.session import asession_result
from pypasser.captcha.turnstile.flow import (
    CHALLENGE_PAGE_MARKERS,
    CHECKBOX_SELECTORS,
    POLL_INTERVAL,
    TOKEN_SELECTORS,
    WIDGET_FRAME_SELECTORS,
    _poll_limit,
    _ScanSchedule,
    _window_left,
)
from pypasser.structs import SolverResult

if TYPE_CHECKING:
    from pypasser.browsers import AsyncBrowserAdapter


class AsyncTurnstileSolver:
    """Asynchronous Cloudflare Turnstile solver (checkbox clicker)."""

    def __init__(self, attempts: int = 3, timeout: float = 30) -> None:
        self.attempts = attempts
        self.timeout = timeout

    async def _result(
        self, token: Optional[str], adapter: "AsyncBrowserAdapter"
    ) -> SolverResult:
        return await asession_result(adapter, token)

    async def solve(self, adapter: "AsyncBrowserAdapter") -> SolverResult:
        token = await self._read_token(adapter)
        if token:
            return await self._result(token, adapter)

        interstitial = await self._is_challenge_page(adapter)
        deadline = time.monotonic() + self.timeout

        remaining = self.attempts
        while remaining and time.monotonic() < deadline:
            frame = await self._find_widget_frame(
                adapter,
                interstitial=interstitial,
                deadline=deadline,
                window=_window_left(deadline),
            )
            if frame:
                await self._click_checkbox(adapter, frame)
                token, cleared = await self._wait_for_token(
                    adapter, until_cleared=interstitial, wait=_window_left(deadline)
                )
                if token or cleared:
                    return await self._result(token, adapter)
            remaining -= 1

        token, cleared = await self._wait_for_token(
            adapter, until_cleared=interstitial, deadline=deadline
        )
        if token or cleared:
            return await self._result(token, adapter)

        return SolverResult(is_solved=False, response_token=None)

    async def _find_widget_frame(
        self,
        adapter: "AsyncBrowserAdapter",
        interstitial: bool = False,
        window: Optional[float] = None,
        deadline: Optional[float] = None,
    ) -> Optional[str]:
        limit = _poll_limit(window, deadline)
        while True:
            for selector in WIDGET_FRAME_SELECTORS:
                try:
                    if await adapter.exists(selector):
                        return selector
                except Exception:
                    continue
            if interstitial:
                try:
                    if await adapter.exists("iframe"):
                        return "iframe"
                except Exception:
                    pass
            if limit is not None and time.monotonic() >= limit:
                return None
            await asyncio.sleep(POLL_INTERVAL)

    async def _click_checkbox(self, adapter: "AsyncBrowserAdapter", frame: str) -> None:
        for selector in CHECKBOX_SELECTORS:
            try:
                if not await adapter.visible(selector, frame=frame):
                    continue
                await adapter.click(selector, frame=frame, timeout=self.timeout)
                return
            except Exception:
                continue

    async def _is_challenge_page(self, adapter: "AsyncBrowserAdapter") -> bool:
        try:
            source = (await adapter.page_source() or "").lower()
        except Exception:
            return False
        return any(marker in source for marker in CHALLENGE_PAGE_MARKERS)

    async def _read_token(self, adapter: "AsyncBrowserAdapter") -> Optional[str]:
        for selector in TOKEN_SELECTORS:
            token = await adapter.attr(selector, "value", timeout=1)
            if token:
                return token
        return None

    async def _wait_for_token(
        self,
        adapter: "AsyncBrowserAdapter",
        wait: Optional[float] = None,
        until_cleared: bool = False,
        deadline: Optional[float] = None,
    ) -> tuple[Optional[str], bool]:
        if deadline is None:
            deadline = time.monotonic() + (self.timeout if wait is None else wait)
        scan = _ScanSchedule()
        while True:
            token = await self._read_token(adapter)
            if token:
                return token, False
            now = time.monotonic()
            if until_cleared and scan.due():
                if not await self._is_challenge_page(adapter):
                    return None, True
            if now >= deadline:
                return None, False
            await asyncio.sleep(POLL_INTERVAL)
