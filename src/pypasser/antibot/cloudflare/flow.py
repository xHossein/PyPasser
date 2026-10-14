"""Engine-agnostic Cloudflare interstitial clearance flow."""

from __future__ import annotations

from typing import Any

from pypasser.captcha.turnstile.flow import CHALLENGE_PAGE_MARKERS, WIDGET_FRAME_SELECTORS
from pypasser.exceptions import CloudflareClearanceError
from pypasser.structs import SolverResult

DEFAULT_TIMEOUT = 60.0
CLEARANCE_COOKIE = "cf_clearance"


def _wall_present(adapter: Any) -> bool:
    """Whether the page currently shows the Cloudflare wall."""
    try:
        source = (adapter.page_source() or "").lower()
    except Exception:
        source = ""
    if any(marker in source for marker in CHALLENGE_PAGE_MARKERS):
        return True
    for selector in WIDGET_FRAME_SELECTORS:
        try:
            if adapter.exists(selector):
                return True
        except Exception:
            continue
    return False


def _session_result(adapter: Any) -> SolverResult:
    """A cleared session: browser cookies plus the UA they are bound to."""
    try:
        cookies = adapter.cookies() or None
    except Exception:
        cookies = None
    try:
        user_agent = adapter.user_agent()
    except Exception:
        user_agent = None
    return SolverResult(
        is_solved=True,
        response_token=None,
        cookies=cookies,
        user_agent=user_agent,
    )


def require_clearance(result: SolverResult) -> None:
    """Reject a pass without the replayable cookie."""
    if CLEARANCE_COOKIE not in (result.cookies or {}):
        raise CloudflareClearanceError(
            "The Cloudflare challenge passed but no cf_clearance cookie came "
            "back. Either the browser adapter cannot expose its cookies, or "
            "Cloudflare cleared the session without issuing clearance "
            "(soft-block) — a datacenter IP is the usual cause."
        )


class CloudflareBypass:
    """Synchronous Cloudflare interstitial bypass."""

    def __init__(self, attempts: int = 3, timeout: float = DEFAULT_TIMEOUT) -> None:
        self.attempts = attempts
        self.timeout = timeout

    def solve(self, page: Any, backend: str = "auto") -> SolverResult:
        from pypasser.browsers import get_adapter
        from pypasser.captcha.turnstile.flow import TurnstileSolver

        adapter = get_adapter(backend, page)

        if not _wall_present(adapter):
            return _session_result(adapter)

        result = TurnstileSolver(attempts=self.attempts, timeout=self.timeout).solve(adapter)
        if result.is_solved:
            require_clearance(result)
            return result

        if not _wall_present(adapter):
            return _session_result(adapter)
        return result
