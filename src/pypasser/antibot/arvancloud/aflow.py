"""Async ArvanCloud anti-bot bypass — mirrors :mod:`flow` step by step.

Only the awaited wire calls live here; the session config, client
construction and result shape come from the shared :class:`_ArvanCore`.
"""

from __future__ import annotations

import asyncio
from typing import Optional

import httpx

from pypasser.antibot.arvancloud.challenge import (
    challenge_cookies,
    cookie_domain,
    is_challenge,
)
from pypasser.antibot.arvancloud.flow import _ArvanCore
from pypasser.exceptions import ArvanBypassError, RequestFailed
from pypasser.structs import SolverResult


class AsyncArvanCloudBypass(_ArvanCore):
    """Asynchronous ArvanCloud anti-bot bypass (``httpx.AsyncClient``)."""

    async def solve(
        self,
        url: str,
        proxy: Optional[str] = None,
        attempts: int = 3,
    ) -> SolverResult:
        """Async version of :meth:`ArvanCloudBypass.solve`."""
        kwargs = self._client_kwargs(proxy)
        async with httpx.AsyncClient(**kwargs) as client:
            domain = cookie_domain(url)
            for attempt in range(attempts):
                response = await self._get(client, url)
                if not is_challenge(response.text):
                    return self._result(client)
                cookies = challenge_cookies(response.text)
                for name, value in cookies.items():
                    client.cookies.set(name, value, domain=domain)
                if attempt < attempts - 1:
                    await asyncio.sleep(0.5 + 0.5 * attempt)
            raise ArvanBypassError(
                f"ArvanCloud challenge not cleared for {url} after {attempts} attempts"
            )

    async def _get(self, client: httpx.AsyncClient, url: str) -> httpx.Response:
        try:
            return await client.get(url, follow_redirects=True)
        except httpx.HTTPError as exc:
            raise RequestFailed(f"request to {url} failed: {exc}") from exc
