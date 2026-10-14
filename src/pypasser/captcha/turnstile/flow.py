"""Engine-agnostic Cloudflare Turnstile solve flow."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Optional

from pypasser.structs import SolverResult

if TYPE_CHECKING:  # pragma: no cover
    from pypasser.browsers import BrowserAdapter

WIDGET_FRAME_SELECTORS = (
    "iframe[src*='challenges.cloudflare.com']",
    ".cf-turnstile iframe",
    "iframe[title*='Cloudflare security challenge']",
)

CHECKBOX_SELECTORS = (
    "input[type='checkbox']",
    "#challenge-stage input[type='checkbox']",
    ".cb-lb",
    "label[for]",
)

TOKEN_SELECTORS = (
    "input[name='cf-turnstile-response']",
    "input[name*='cf-turnstile-response']",
)

POLL_INTERVAL = 0.25
ATTEMPT_WINDOW = 5.0

CHALLENGE_PAGE_MARKERS = (
    "just a moment",
    "checking your browser",
    "enable javascript and cookies to continue",
)


def _window_left(deadline: float) -> float:
    return min(ATTEMPT_WINDOW, max(deadline - time.monotonic(), 0.0))


def _poll_limit(window: Optional[float], deadline: Optional[float]) -> Optional[float]:
    bounds = [
        limit
        for limit in (
            None if window is None else time.monotonic() + window,
            deadline,
        )
        if limit is not None
    ]
    return min(bounds) if bounds else None


class _ScanSchedule:
    def __init__(self) -> None:
        self.interval = max(POLL_INTERVAL * 4, 1.0)
        self.next_scan = time.monotonic()

    def due(self) -> bool:
        now = time.monotonic()
        if now < self.next_scan:
            return False
        self.next_scan = now + self.interval
        return True


def _session_result(
    token: Optional[str], cookies: Optional[dict], user_agent: Optional[str]
) -> SolverResult:
    return SolverResult(
        is_solved=True,
        response_token=token,
        cookies=cookies,
        user_agent=user_agent,
    )


class TurnstileSolver:
    """Synchronous Cloudflare Turnstile solver."""

    def __init__(self, attempts: int = 3, timeout: float = 30) -> None:
        self.attempts = attempts
        self.timeout = timeout

    def _result(self, token: Optional[str], adapter: "BrowserAdapter") -> SolverResult:
        try:
            cookies = adapter.cookies() or None
        except Exception:
            cookies = None
        try:
            user_agent = adapter.user_agent()
        except Exception:
            user_agent = None
        return _session_result(token, cookies, user_agent)

    def solve(self, adapter: "BrowserAdapter") -> SolverResult:
        token = self._read_token(adapter)
        if token:
            return self._result(token, adapter)

        interstitial = self._is_challenge_page(adapter)
        deadline = time.monotonic() + self.timeout

        remaining = self.attempts
        while remaining and time.monotonic() < deadline:
            frame = self._find_widget_frame(
                adapter,
                interstitial=interstitial,
                deadline=deadline,
                window=_window_left(deadline),
            )
            if frame:
                self._click_checkbox(adapter, frame)
                token, cleared = self._wait_for_token(
                    adapter, until_cleared=interstitial, wait=_window_left(deadline)
                )
                if token or cleared:
                    return self._result(token, adapter)
            remaining -= 1

        token, cleared = self._wait_for_token(
            adapter, until_cleared=interstitial, deadline=deadline
        )
        if token or cleared:
            return self._result(token, adapter)

        return SolverResult(is_solved=False, response_token=None)

    def _find_widget_frame(
        self,
        adapter: "BrowserAdapter",
        interstitial: bool = False,
        window: Optional[float] = None,
        deadline: Optional[float] = None,
    ) -> Optional[str]:
        limit = _poll_limit(window, deadline)
        while True:
            for selector in WIDGET_FRAME_SELECTORS:
                try:
                    if adapter.exists(selector):
                        return selector
                except Exception:
                    continue
            if interstitial:
                try:
                    if adapter.exists("iframe"):
                        return "iframe"
                except Exception:
                    pass
            if limit is not None and time.monotonic() >= limit:
                return None
            time.sleep(POLL_INTERVAL)

    def _click_checkbox(self, adapter: "BrowserAdapter", frame: str) -> None:
        for selector in CHECKBOX_SELECTORS:
            try:
                if not adapter.visible(selector, frame=frame):
                    continue
                adapter.click(selector, frame=frame, timeout=self.timeout)
                return
            except Exception:
                continue

    def _is_challenge_page(self, adapter: "BrowserAdapter") -> bool:
        try:
            source = (adapter.page_source() or "").lower()
        except Exception:
            return False
        return any(marker in source for marker in CHALLENGE_PAGE_MARKERS)

    def _read_token(self, adapter: "BrowserAdapter") -> Optional[str]:
        for selector in TOKEN_SELECTORS:
            token = adapter.attr(selector, "value", timeout=1)
            if token:
                return token
        return None

    def _wait_for_token(
        self,
        adapter: "BrowserAdapter",
        wait: Optional[float] = None,
        until_cleared: bool = False,
        deadline: Optional[float] = None,
    ) -> tuple[Optional[str], bool]:
        if deadline is None:
            deadline = time.monotonic() + (self.timeout if wait is None else wait)
        scan = _ScanSchedule()
        while True:
            token = self._read_token(adapter)
            if token:
                return token, False
            now = time.monotonic()
            if until_cleared and scan.due():
                if not self._is_challenge_page(adapter):
                    return None, True
            if now >= deadline:
                return None, False
            time.sleep(POLL_INTERVAL)
