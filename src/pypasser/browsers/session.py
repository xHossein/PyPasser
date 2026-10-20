"""Build a cleared-session :class:`SolverResult` from a browser adapter."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from pypasser.structs import SolverResult

if TYPE_CHECKING:  # pragma: no cover
    from pypasser.browsers import AsyncBrowserAdapter, BrowserAdapter


def _build(
    response_token: Optional[str],
    cookies: Optional[dict[str, str]],
    user_agent: Optional[str],
) -> SolverResult:
    return SolverResult(
        is_solved=True,
        response_token=response_token,
        cookies=cookies,
        user_agent=user_agent,
    )


def session_result(
    adapter: "BrowserAdapter", response_token: Optional[str] = None
) -> SolverResult:
    """A solved result carrying the adapter's cookies and UA."""
    try:
        cookies = adapter.cookies() or None
    except Exception:
        cookies = None
    try:
        user_agent = adapter.user_agent()
    except Exception:
        user_agent = None
    return _build(response_token, cookies, user_agent)


async def asession_result(
    adapter: "AsyncBrowserAdapter", response_token: Optional[str] = None
) -> SolverResult:
    """Async version of :func:`session_result`."""
    try:
        cookies = await adapter.cookies() or None
    except Exception:
        cookies = None
    try:
        user_agent = await adapter.user_agent()
    except Exception:
        user_agent = None
    return _build(response_token, cookies, user_agent)


__all__ = ["asession_result", "session_result"]
