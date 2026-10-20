"""Browserless ARCaptcha solver (HTTP only).

The widget is a pure HTTP client behind the scenes: it POSTs obfuscated
JSON to ``api.arcaptcha.ir`` (see :mod:`codec`), gets image/audio paths
back, and answers with another obfuscated POST. This module replays that
protocol directly.

Supported challenge types:

``puzzle``
    Slider puzzle — solved with CV (:mod:`puzzle`).
``question``
    9-image grid. Falls back to the widget's own voice variant (the API
    hands out a standalone voice challenge that is accepted for the same
    site key), transcribed with Persian ASR (:mod:`voice`).
``voice``
    Persian spoken word — transcribed the same way.
``cookie`` / ``accept``
    Server-side pass — no work needed; the token is the challenge id.

``block``
    The server flagged the session (usually a bad bowman). Retrying with a
    fresh bowman is what the widget's own "reset challenge" does.

Sync and async variants (:mod:`asolver`) share the session state and the
pure payload logic through :class:`_ARCore`; each transport only implements
its own wire calls.
"""

from __future__ import annotations

import io
import random
import tempfile
import time
from typing import Any, Optional, Union

import httpx

from pypasser.captcha.arcaptcha.bowman import build_bowman
from pypasser.captcha.arcaptcha.codec import db_decode, ob_encode
from pypasser.captcha.arcaptcha.constants import (
    API_BASE,
    BLOCK_TYPE,
    DEFAULT_UA,
    INSTANT_TYPES,
    VOICE_ANSWER_TYPE,
    VOICE_TYPES,
)
from pypasser.captcha.arcaptcha.puzzle import solve_puzzle
from pypasser.captcha.arcaptcha.voice import transcribe
from pypasser.exceptions import (
    ARCaptchaBlocked,
    ARCaptchaSolveFailed,
    RequestFailed,
)
from pypasser.proxies import httpx_client_kwargs
from pypasser.speech import cleanup_audio


def _headers(domain: str, lang: str, ua: str) -> dict[str, str]:
    """Per-request headers the widget sends (they are checked)."""
    return {
        "Content-Type": "application/octet-stream",
        "Content-Language": lang,
        "Origin": f"https://{domain}",
        "Referer": f"https://{domain}/",
        "User-Agent": ua,
    }


def _client_kwargs(
    proxy: Union[str, None], timeout: Union[int, float], ua: str
) -> dict[str, Any]:
    return httpx_client_kwargs(timeout, {"User-Agent": ua}, proxy)


class _ARCore:
    """Session state + transport-free payload logic shared by both variants."""

    def __init__(
        self,
        site_key: str,
        domain: str,
        *,
        proxy: Union[str, None] = None,
        timeout: Union[int, float] = 20,
        user_agent: str = DEFAULT_UA,
        lang: str = "fa",
        min_drag_time: float = 1.2,
        max_drag_time: float = 2.5,
        voice_model: Union[str, None] = None,
    ) -> None:
        self.site_key = site_key
        self.domain = domain
        self.lang = lang
        self.user_agent = user_agent
        self.min_drag_time = min_drag_time
        self.max_drag_time = max_drag_time
        self.voice_model = voice_model
        self.timeout = timeout
        self.proxy = proxy

    def _bowman(self) -> dict[str, Any]:
        """A fresh session profile (per create attempt — a block is per-session)."""
        return build_bowman(self.site_key, self.domain, lang=self.lang)

    def _create_params(self, bowman: dict[str, Any]) -> dict[str, str]:
        return {"id": bowman["bowman_id"], "site_key": self.site_key}

    def _answer_params(self) -> dict[str, str]:
        return {"site_key": self.site_key}

    def _puzzle_urls(self, content: dict[str, Any]) -> tuple[str, str]:
        base = f"puzzles/{self.site_key}/x/"
        return base + content["puzzle_background"], base + content["puzzle_piece"]

    def _puzzle_payload(self, challenge_id: str, x: int) -> dict[str, Any]:
        return {
            "challenge_id": challenge_id,
            "answers": x,
            "site_key": self.site_key,
            "drag_drop": round(random.uniform(1.0, 1.8), 2),
            "drag_drop_time": int(
                random.uniform(self.min_drag_time, self.max_drag_time) * 1000
            ),
        }

    def _voice_payload(self, challenge_id: str, text: str) -> dict[str, Any]:
        return {
            "challenge_id": challenge_id,
            "answers": text,
            "site_key": self.site_key,
            "captcha_type": VOICE_ANSWER_TYPE,
        }


class ARCaptchaSolver(_ARCore):
    """Synchronous ARCaptcha solver.

    Parameters
    ----------
    site_key: str
        The target's ARCaptcha site key.
    domain: str
        Domain the widget is embedded on (must be registered for the key).
    """

    def solve(self, attempts: int = 3) -> str:
        """Solve a challenge and return its token (the challenge id)."""
        last: Optional[Exception] = None
        with httpx.Client(**_client_kwargs(self.proxy, self.timeout, self.user_agent)) as client:
            for attempt in range(attempts):
                try:
                    return self._solve_once(client)
                except ARCaptchaBlocked:
                    if attempt == attempts - 1:
                        raise
                    time.sleep(1.0 + random.random())
                except (ARCaptchaSolveFailed, RequestFailed) as exc:
                    last = exc
                    if attempt == attempts - 1:
                        raise
                    time.sleep(0.5 + random.random() * 0.5)
        raise ARCaptchaSolveFailed(f"exhausted attempts: {last}")  # pragma: no cover

    def _post(self, client: httpx.Client, path: str, payload: Any, params: dict[str, str]) -> Any:
        resp = client.post(
            f"{API_BASE}/{path}",
            params=params,
            content=ob_encode(payload),
            headers=_headers(self.domain, self.lang, self.user_agent),
        )
        try:
            return db_decode(resp.content)
        except Exception as exc:
            raise RequestFailed(f"ARCaptcha API returned undecodable body: {exc}") from exc

    def _get(self, client: httpx.Client, path: str) -> bytes:
        url = f"{API_BASE}/{path}"
        resp = client.get(url, headers=_headers(self.domain, self.lang, self.user_agent))
        resp.raise_for_status()
        return resp.content

    def _create(self, client: httpx.Client, path: str = "create") -> Any:
        bowman = self._bowman()
        return self._post(client, path, bowman, self._create_params(bowman))

    def _answer(self, client: httpx.Client, payload: dict[str, Any]) -> Any:
        return self._post(client, "answer", payload, self._answer_params())

    def _solve_once(self, client: httpx.Client) -> str:
        data = self._create(client)
        payload = self._answer_payload(client, data)
        if payload is None:
            return str(data["content"]["challenge_id"])
        result = self._answer(client, payload)
        if isinstance(result, dict) and result.get("success"):
            return str(payload["challenge_id"])
        raise ARCaptchaSolveFailed(f"answer rejected: {result}")

    def _answer_payload(
        self, client: httpx.Client, data: dict[str, Any]
    ) -> Optional[dict[str, Any]]:
        """Build the answer payload for a create response.

        Returns ``None`` for the instant-pass types (nothing to answer).
        """
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
                challenge_id, self._solve_puzzle(client, content)
            )

        if captcha_type in VOICE_TYPES:
            voice = self._solve_voice(client)
            return self._voice_payload(voice["challenge_id"], voice["text"])

        raise ARCaptchaSolveFailed(f"unsupported captcha_type {captcha_type!r}")

    def _solve_puzzle(self, client: httpx.Client, content: dict[str, Any]) -> int:
        from PIL import Image

        bg_url, piece_url = self._puzzle_urls(content)
        bg = Image.open(io.BytesIO(self._get(client, bg_url)))
        piece = Image.open(io.BytesIO(self._get(client, piece_url)))
        try:
            return solve_puzzle(bg, piece, int(content["y"])).x
        except ValueError as exc:
            raise ARCaptchaSolveFailed(f"puzzle CV failed: {exc}") from exc

    def _solve_voice(self, client: httpx.Client) -> dict[str, Any]:
        data = self._create(client, "create/voice")
        content = data.get("content") or {}
        path = content.get("path")
        if not path:
            raise ARCaptchaSolveFailed(f"voice create failed: {data}")
        audio = self._get(client, f"voices/{path}")
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            tmp.write(audio)
            tmp_path = tmp.name
        try:
            if self.voice_model:
                text = transcribe(tmp_path, self.voice_model)
            else:
                text = transcribe(tmp_path)
        finally:
            cleanup_audio(tmp_path)
        if not text:
            raise ARCaptchaSolveFailed("transcription empty")
        return {"challenge_id": content["challenge_id"], "text": text}


__all__ = ["ARCaptchaSolver"]
