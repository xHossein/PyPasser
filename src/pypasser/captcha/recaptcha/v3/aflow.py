"""Asynchronous reCaptcha V3 HTTP flow."""

from __future__ import annotations

import httpx

from pypasser.captcha.recaptcha.v3.flow import (
    _client_kwargs,
    _V3Core,
    _wrap_request_error,
)
from pypasser.captcha.recaptcha.v3.render import alatest_render_version
from pypasser.structs import SolverResult


class AsyncV3Solver(_V3Core):
    """Asynchronous reCaptcha V3 bypass (HTTP only)."""

    async def solve(self) -> SolverResult:
        async with httpx.AsyncClient(**_client_kwargs(self.proxy, self.timeout)) as client:
            return await self._run(client)

    async def _run(self, client: httpx.AsyncClient) -> SolverResult:
        self.v = (
            await alatest_render_version(client=client, endpoint=self.parsed.endpoint)
        ) or self.v

        try:
            anchor_resp = await client.get(self._token_url(), params=self._anchor_params())
        except httpx.RequestError as exc:
            raise _wrap_request_error(exc) from exc

        token = self._extract_token(anchor_resp.text)

        try:
            reload_resp = await client.post(
                self._reload_url(), content=self._post_data(token), params=f"k={self.k}"
            )
        except httpx.RequestError as exc:
            raise _wrap_request_error(exc) from exc

        return SolverResult(is_solved=True, response_token=self._extract_response(reload_resp.text))
