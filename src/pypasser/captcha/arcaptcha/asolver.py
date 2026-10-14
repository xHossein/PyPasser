"""Async ARCaptcha solver — mirrors :mod:`solver` step by step."""

from __future__ import annotations

import asyncio
import io
import os
import random
import tempfile
from typing import Any, Optional

import httpx

from pypasser.captcha.arcaptcha.codec import db_decode, ob_encode
from pypasser.captcha.arcaptcha.constants import (
    API_BASE,
    BLOCK_TYPE,
    INSTANT_TYPES,
    VOICE_TYPES,
)
from pypasser.captcha.arcaptcha.puzzle import solve_puzzle
from pypasser.captcha.arcaptcha.solver import _ARCore, _client_kwargs, _headers
from pypasser.captcha.arcaptcha.voice import transcribe
from pypasser.exceptions import (
    ARCaptchaBlocked,
    ARCaptchaSolveFailed,
    RequestFailed,
)


class AsyncARCaptchaSolver(_ARCore):
    """Asynchronous ARCaptcha solver (``httpx.AsyncClient``)."""

    async def solve(self, attempts: int = 3) -> str:
        """Solve a challenge and return its token (the challenge id)."""
        last: Optional[Exception] = None
        client_kwargs = _client_kwargs(self.proxy, self.timeout, self.user_agent)
        async with httpx.AsyncClient(**client_kwargs) as client:
            for attempt in range(attempts):
                try:
                    return await self._solve_once(client)
                except ARCaptchaBlocked:
                    if attempt == attempts - 1:
                        raise
                    await asyncio.sleep(1.0 + random.random())
                except (ARCaptchaSolveFailed, RequestFailed) as exc:
                    last = exc
                    if attempt == attempts - 1:
                        raise
                    await asyncio.sleep(0.5 + random.random() * 0.5)
        raise ARCaptchaSolveFailed(f"exhausted attempts: {last}")  # pragma: no cover

    async def _post(
        self,
        client: httpx.AsyncClient,
        path: str,
        payload: Any,
        params: dict[str, str],
    ) -> Any:
        resp = await client.post(
            f"{API_BASE}/{path}",
            params=params,
            content=ob_encode(payload),
            headers=_headers(self.domain, self.lang, self.user_agent),
        )
        try:
            return db_decode(resp.content)
        except Exception as exc:
            raise RequestFailed(f"ARCaptcha API returned undecodable body: {exc}") from exc

    async def _get(self, client: httpx.AsyncClient, path: str) -> bytes:
        url = f"{API_BASE}/{path}"
        resp = await client.get(url, headers=_headers(self.domain, self.lang, self.user_agent))
        resp.raise_for_status()
        return resp.content

    async def _create(self, client: httpx.AsyncClient, path: str = "create") -> Any:
        bowman = self._bowman()
        return await self._post(
            client, path, bowman, self._create_params(bowman)
        )

    async def _answer(self, client: httpx.AsyncClient, payload: dict[str, Any]) -> Any:
        return await self._post(client, "answer", payload, self._answer_params())

    async def _solve_once(self, client: httpx.AsyncClient) -> str:
        data = await self._create(client)
        payload = await self._answer_payload(client, data)
        if payload is None:
            return str(data["content"]["challenge_id"])
        result = await self._answer(client, payload)
        if isinstance(result, dict) and result.get("success"):
            return str(payload["challenge_id"])
        raise ARCaptchaSolveFailed(f"answer rejected: {result}")

    async def _answer_payload(
        self, client: httpx.AsyncClient, data: dict[str, Any]
    ) -> Optional[dict[str, Any]]:
        """Build the answer payload for a create response (``None`` = instant pass)."""
        captcha_type = data.get("captcha_type")
        content = data.get("content") or {}
        challenge_id = content.get("challenge_id")
        if not challenge_id:
            raise ARCaptchaSolveFailed(f"create response without challenge_id: {data}")

        if captcha_type in INSTANT_TYPES:
            return None

        if captcha_type == BLOCK_TYPE:
            raise ARCaptchaBlocked(f"server blocked session for {self.domain}")

        if captcha_type == "puzzle":
            return self._puzzle_payload(
                challenge_id, await self._solve_puzzle(client, content)
            )

        if captcha_type in VOICE_TYPES:
            voice = await self._solve_voice(client)
            return self._voice_payload(voice["challenge_id"], voice["text"])

        raise ARCaptchaSolveFailed(f"unsupported captcha_type {captcha_type!r}")

    async def _solve_puzzle(self, client: httpx.AsyncClient, content: dict[str, Any]) -> int:
        from PIL import Image

        bg_url, piece_url = self._puzzle_urls(content)
        bg = Image.open(io.BytesIO(await self._get(client, bg_url)))
        piece = Image.open(io.BytesIO(await self._get(client, piece_url)))

        def _solve() -> int:
            try:
                return solve_puzzle(bg, piece, int(content["y"])).x
            except ValueError as exc:
                raise ARCaptchaSolveFailed(f"puzzle CV failed: {exc}") from exc

        return await asyncio.get_event_loop().run_in_executor(None, _solve)

    async def _solve_voice(self, client: httpx.AsyncClient) -> dict[str, Any]:
        data = await self._create(client, "create/voice")
        content = data.get("content") or {}
        path = content.get("path")
        if not path:
            raise ARCaptchaSolveFailed(f"voice create failed: {data}")
        audio = await self._get(client, f"voices/{path}")
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            tmp.write(audio)
            tmp_path = tmp.name
        loop = asyncio.get_event_loop()
        try:
            if self.voice_model:
                text = await loop.run_in_executor(
                    None, transcribe, tmp_path, self.voice_model
                )
            else:
                text = await loop.run_in_executor(None, transcribe, tmp_path)
        finally:
            os.unlink(tmp_path)
            wav = tmp_path.replace(".mp3", ".wav")
            if os.path.exists(wav):
                os.unlink(wav)
        if not text:
            raise ARCaptchaSolveFailed("transcription empty")
        return {"challenge_id": content["challenge_id"], "text": text}
