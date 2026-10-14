"""Browserless ArvanCloud anti-bot bypass (cookie replay).

ArvanCloud's interstitial is pure JavaScript: the challenge page only
computes two cookies (``__arcsjs`` / ``__arcsjsc``) and reloads. Replaying
the same two requests a browser would make — first the plain page, then the
same page with the decoded cookies set — lands on the real content, so no
browser or JS engine is involved (see :mod:`challenge` for the decoding).

The cleared cookies are returned on the :class:`SolverResult` so the caller
can reuse the session over plain HTTP; they are bound to the visitor's IP
and User-Agent, like Cloudflare's ``cf_clearance``.
"""

from __future__ import annotations

import time
from typing import Any, Optional, Union

import httpx

from pypasser.antibot.arvancloud.challenge import (
    challenge_cookies,
    cookie_domain,
    is_challenge,
)
from pypasser.exceptions import ArvanBypassError, RequestFailed
from pypasser.structs import SolverResult

DEFAULT_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"
)


class _ArvanCore:
    """Session config shared by the sync/async bypasses."""

    def __init__(
        self,
        timeout: Union[int, float] = 30,
        user_agent: str = DEFAULT_UA,
    ) -> None:
        self.timeout = timeout
        self.user_agent = user_agent

    def _result(self, client: "httpx.Client | httpx.AsyncClient") -> SolverResult:
        return SolverResult(
            is_solved=True,
            response_token=None,
            cookies=_context_cookies(client),
            user_agent=self.user_agent,
        )

    def _client_kwargs(self, proxy: Optional[str]) -> dict[str, Any]:
        kwargs: dict[str, Any] = {
            "timeout": self.timeout,
            "headers": {"User-Agent": self.user_agent},
        }
        if proxy:
            from pypasser.proxies import build_httpx_mounts

            mounts = build_httpx_mounts(proxy)
            if mounts is not None:
                kwargs["mounts"] = mounts
        return kwargs


class ArvanCloudBypass(_ArvanCore):
    """Synchronous ArvanCloud anti-bot bypass."""

    def solve(
        self,
        url: str,
        proxy: Optional[str] = None,
        attempts: int = 3,
    ) -> SolverResult:
        """Clear the ArvanCloud challenge for ``url`` and return the session.

        Parameters
        ----------
        url: str
            Any page of the protected site.
        proxy: str, optional
            Proxy URL (the clearance is tied to the exit IP).
        attempts: int
            How many challenge/answer round trips to try — each attempt
            decodes a freshly served challenge page.
        """
        kwargs = self._client_kwargs(proxy)
        client = httpx.Client(**kwargs)
        try:
            domain = cookie_domain(url)
            for attempt in range(attempts):
                response = self._get(client, url)
                if not is_challenge(response.text):
                    return self._result(client)
                cookies = challenge_cookies(response.text)
                for name, value in cookies.items():
                    client.cookies.set(name, value, domain=domain)
                if attempt < attempts - 1:
                    time.sleep(0.5 + 0.5 * attempt)
            raise ArvanBypassError(
                f"ArvanCloud challenge not cleared for {url} after {attempts} attempts"
            )
        finally:
            client.close()

    def _get(self, client: httpx.Client, url: str) -> httpx.Response:
        try:
            return client.get(url, follow_redirects=True)
        except httpx.HTTPError as exc:
            raise RequestFailed(f"request to {url} failed: {exc}") from exc


def _context_cookies(client: "httpx.Client | httpx.AsyncClient") -> dict[str, str]:
    """Cookies collected on the client, as ``name -> value``."""
    try:
        return {cookie.name: cookie.value or "" for cookie in client.cookies.jar}
    except Exception:
        return {}
