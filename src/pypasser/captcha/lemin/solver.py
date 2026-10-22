"""Lemin cropped captcha solver (HTTP only).

The widget is three HTTP calls, all against ``api.leminnow.com``:

1. ``GET .../image/<challenge_id>`` — returns ``"<image url>|<caption>"`` as
   ``text/plain``. A third ``|`` segment, when present, is base64
   ``"<pieces>,<base>,<margin>"`` and overrides the layout defaults.
2. Solve the scene with :mod:`pypasser.captcha.lemin.vision`.
3. ``POST .../pre-validate`` with ``{"answer", "challenge_id"}``; the reply's
   ``data.pv_token`` is what the site submits.

The image URL is signed as ``md5(url_with_query + SECRET)`` and passed as
``lsign``; without it the endpoint answers 403. The secret ships inside every
copy of the cropped bundle.

A challenge is single-use: a rejected answer deactivates it, so a wrong
destination cannot be retried — the solver raises and the caller starts over
with a fresh challenge.
"""

from __future__ import annotations

import random
import time
from typing import Any, Optional, Union

import httpx

from pypasser.captcha.lemin.answers import drag_path, encode, multi_drag_path
from pypasser.captcha.lemin.constants import DEFAULT_UA, HISTORY, SCENE_WIDTH
from pypasser.captcha.lemin.transport import (
    DEFAULT_SCREEN,
    Challenge,
    check_image_response,
    check_verify_response,
    decode_challenge,
    image_url,
    new_challenge_id,
    parse_image,
    parse_verify,
    pre_validate_url,
)
from pypasser.captcha.lemin.vision import solve_image
from pypasser.exceptions import LeminSolveFailed, RequestFailed
from pypasser.proxies import httpx_client_kwargs


class _LeminCore:
    """Transport-free challenge logic shared by the sync and async variants."""

    def __init__(
        self,
        captcha_id: str,
        domain: str,
        *,
        proxy: Union[str, None] = None,
        timeout: Union[int, float] = 20,
        user_agent: str = DEFAULT_UA,
        screen: tuple[int, int] = DEFAULT_SCREEN,
        jitter: float = 3.0,
    ) -> None:
        self.captcha_id = captcha_id
        self.domain = domain.rstrip("/")
        self.proxy = proxy
        self.timeout = timeout
        self.user_agent = user_agent
        self.screen = screen
        self.jitter = jitter

    def _headers(self, extra: Optional[dict[str, str]] = None) -> dict[str, str]:
        headers = {
            "Origin": self.domain,
            "Referer": f"{self.domain}/",
            "User-Agent": self.user_agent,
        }
        if extra:
            headers.update(extra)
        return headers

    def _client_kwargs(self) -> dict[str, Any]:
        return httpx_client_kwargs(self.timeout, self._headers(), self.proxy)

    def _image_url(self, challenge_id: str) -> str:
        return image_url(self.captcha_id, self.domain, challenge_id, self.screen)

    def _pre_validate_url(self) -> str:
        return pre_validate_url()

    def _decode_challenge(self, challenge_id: str, body: str, image: Any) -> Challenge:
        return decode_challenge(challenge_id, body, image)

    def answer_for(self, challenge: Challenge, rng: Optional[random.Random] = None) -> str:
        """Build the ``answer`` value for a decoded challenge."""
        rng = rng or random.Random()
        destinations = self._destinations(challenge)
        if challenge.pieces > 1:
            path = multi_drag_path(destinations, rng=rng)
        else:
            path = drag_path(destinations[0], jitter=self.jitter, rng=rng)
        return encode(path[-HISTORY:])

    def _destinations(self, challenge: Challenge) -> list[tuple[int, int]]:
        """Destination ``(left, top)`` per piece, in natural pixels."""
        if challenge.pieces == 1:
            return [solve_image(challenge.image, SCENE_WIDTH)]
        raise LeminSolveFailed(
            "multi-piece cropped challenges are not supported yet "
            f"(this challenge asks for {challenge.pieces} pieces)"
        )

    def _parse_verify(self, payload: Any) -> str:
        return parse_verify(payload)

    def _new_challenge_id(self) -> str:
        return new_challenge_id()


class LeminSolver(_LeminCore):
    """Synchronous Lemin cropped solver.

    Parameters
    ----------
    captcha_id: str
        The target's Lemin captcha id (``CROPPED_...``).
    domain: str
        Origin the widget is embedded on, e.g. ``"https://example.com"``.
    """

    def solve(self, attempts: int = 3) -> tuple[str, str, str]:
        """Solve a challenge and return ``(pv_token, answer, challenge_id)``."""
        last: Optional[Exception] = None
        with httpx.Client(**self._client_kwargs()) as client:
            for attempt in range(attempts):
                try:
                    return self._solve_once(client)
                except LeminSolveFailed as exc:
                    last = exc
                    if attempt == attempts - 1:
                        raise
                    time.sleep(0.4 + random.random() * 0.6)
        raise LeminSolveFailed(f"exhausted attempts: {last}")  # pragma: no cover

    def _solve_once(self, client: httpx.Client) -> tuple[str, str, str]:
        challenge = self._fetch(client)
        answer = self.answer_for(challenge)
        token = self._verify(client, challenge.challenge_id, answer)
        return token, answer, challenge.challenge_id

    def _fetch(self, client: httpx.Client) -> Challenge:
        challenge_id = self._new_challenge_id()
        response = client.get(self._image_url(challenge_id))
        body = check_image_response(response)
        parts = body.split("|")
        image = self._download(client, parts[0].strip())
        return self._decode_challenge(challenge_id, body, image)

    def _download(self, client: httpx.Client, url: str) -> Any:
        last: Optional[Exception] = None
        for _ in range(4):
            try:
                raw = client.get(url).content
                return parse_image(raw)
            except Exception as exc:  # CDN hiccup, partial body, bad PNG
                last = exc
                time.sleep(1.5)
        raise RequestFailed(f"could not download the Lemin scene: {last}")

    def _verify(self, client: httpx.Client, challenge_id: str, answer: str) -> str:
        response = client.post(
            self._pre_validate_url(),
            json={"answer": answer, "challenge_id": challenge_id},
            headers=self._headers({"Accept": "application/json"}),
        )
        return self._parse_verify(check_verify_response(response))


__all__ = ["Challenge", "LeminSolver"]
