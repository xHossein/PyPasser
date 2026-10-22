"""Async Lemin cropped solver"""

from __future__ import annotations

import asyncio
import random
from typing import Any, Optional

import httpx

from pypasser.captcha.lemin.solver import _LeminCore
from pypasser.captcha.lemin.transport import (
    Challenge,
    check_image_response,
    check_verify_response,
    parse_image,
)
from pypasser.exceptions import LeminSolveFailed, RequestFailed


class AsyncLeminSolver(_LeminCore):
    """Asynchronous Lemin cropped solver (``httpx.AsyncClient``)."""

    async def solve(self, attempts: int = 3) -> tuple[str, str, str]:
        """Solve a challenge and return ``(pv_token, answer, challenge_id)``."""
        last: Optional[Exception] = None
        async with httpx.AsyncClient(**self._client_kwargs()) as client:
            for attempt in range(attempts):
                try:
                    return await self._solve_once(client)
                except LeminSolveFailed as exc:
                    last = exc
                    if attempt == attempts - 1:
                        raise
                    await asyncio.sleep(0.4 + random.random() * 0.6)
        raise LeminSolveFailed(f"exhausted attempts: {last}")  # pragma: no cover

    async def _solve_once(self, client: httpx.AsyncClient) -> tuple[str, str, str]:
        challenge = await self._fetch(client)
        answer = self.answer_for(challenge)
        token = await self._verify(client, challenge.challenge_id, answer)
        return token, answer, challenge.challenge_id

    async def _fetch(self, client: httpx.AsyncClient) -> Challenge:
        challenge_id = self._new_challenge_id()
        response = await client.get(self._image_url(challenge_id))
        body = check_image_response(response)
        parts = body.split("|")
        image = await self._download(client, parts[0].strip())
        return self._decode_challenge(challenge_id, body, image)

    async def _download(self, client: httpx.AsyncClient, url: str) -> Any:
        last: Optional[Exception] = None
        for _ in range(4):
            try:
                raw = (await client.get(url)).content
                return parse_image(raw)
            except Exception as exc:  # CDN hiccup, partial body, bad PNG
                last = exc
                await asyncio.sleep(1.5)
        raise RequestFailed(f"could not download the Lemin scene: {last}")

    async def _verify(
        self, client: httpx.AsyncClient, challenge_id: str, answer: str
    ) -> str:
        response = await client.post(
            self._pre_validate_url(),
            json={"answer": answer, "challenge_id": challenge_id},
            headers=self._headers({"Accept": "application/json"}),
        )
        return self._parse_verify(check_verify_response(response))


__all__ = ["AsyncLeminSolver"]
