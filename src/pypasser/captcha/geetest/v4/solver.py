"""Synchronous GeeTest V4 solver"""

from __future__ import annotations

import random
import time
from typing import Any, Union

import httpx

from pypasser.captcha.geetest.v4 import answers
from pypasser.captcha.geetest.v4.answers import svg_icon
from pypasser.captcha.geetest.v4.protocol import crypto, keyring
from pypasser.captcha.geetest.v4.protocol import pow as pow_module
from pypasser.captcha.geetest.v4.protocol.constants import DEFAULT_LANG, DEFAULT_UA
from pypasser.captcha.geetest.v4.protocol.transport import (
    asset_url,
    callback_name,
    client_kwargs,
    load_url,
    request,
    require_data,
    unwrap,
    verify_url,
)
from pypasser.exceptions import GeeTestError, GeeTestSolveFailed, RequestFailed

# risk_types this solver can answer today. ``icon`` and ``nine`` are answered
# through the audio fallback rather than a classifier (see ANSWER_ORDER).
SUPPORTED_RISK_TYPES = (
    "slide",
    "ai",
    "winlinze",
    "match",
    "nine",
    "icon",
    "svg_icon",
    "voice",
)

ANSWER_ORDER = {
    "slide": ("own", "voice"),
    "ai": ("own", "voice"),
    "winlinze": ("own", "voice"),
    "match": ("own", "voice"),
    "nine": ("voice",),
    "icon": ("voice",),
    "svg_icon": ("voice", "own"),
    "voice": ("voice",),
}

# Server verdicts that mean the signature was rejected rather than the answer.
_DECRYPT_ERROR_CODES = (-50002, -50003)
_SWEEPS = 2


class _V4Core:
    """Decisions shared by the sync and async solvers."""

    def __init__(
        self,
        captcha_id: str,
        *,
        risk_type: str = "auto",
        proxy: Union[str, None] = None,
        timeout: Union[int, float] = 20,
        user_agent: str = DEFAULT_UA,
        lang: str = DEFAULT_LANG,
        voice_model_path: Union[str, None] = None,
    ) -> None:
        if risk_type != "auto" and risk_type not in SUPPORTED_RISK_TYPES:
            raise GeeTestError(
                f"risk_type {risk_type!r} is not supported; use 'auto' or one "
                f"of {', '.join(SUPPORTED_RISK_TYPES)}"
            )
        self.captcha_id = captcha_id
        self.requested_risk_type = risk_type
        self.risk_type = risk_type
        self.proxy = proxy
        self.timeout = timeout
        self.user_agent = user_agent
        self.lang = lang
        self.voice_model_path = voice_model_path
        self._script_cache: dict[str, str] = {}

    def _client_kwargs(self) -> dict[str, Any]:
        return client_kwargs(self.proxy, self.timeout, self.user_agent)

    @staticmethod
    def _parse_load(response: dict[str, Any]) -> dict[str, Any]:
        require_data(
            response, "lot_number", "pow_detail", "payload", "process_token"
        )
        return response

    def _parse_auto(self, probe: dict[str, Any]) -> dict[str, Any]:
        self._parse_load(probe)
        captcha_type = probe.get("captcha_type", "slide")
        if captcha_type not in ANSWER_ORDER:
            raise GeeTestError(
                f"captcha id serves an unsupported challenge type {captcha_type!r}"
            )
        self.risk_type = captcha_type
        return probe

    @staticmethod
    def _seccode(response: dict[str, Any]) -> dict[str, Any]:
        seccode = response["seccode"]
        if not isinstance(seccode, dict):
            raise GeeTestSolveFailed(f"unexpected seccode shape: {seccode!r}")
        return seccode

    @staticmethod
    def _verdict(response: dict[str, Any]) -> str:
        if response.get("result") == "success" and response.get("seccode"):
            return "success"
        for raw in (response.get("code"), response.get("status")):
            if raw is None:
                continue
            try:
                if int(raw) in _DECRYPT_ERROR_CODES:
                    return "rekey"
            except (TypeError, ValueError):
                continue
        return "rejected"

    def _should_recover(self, verdict: str, sweep: int) -> bool:
        """Whether to refresh the signing key and sweep again."""
        if sweep >= _SWEEPS - 1:
            return False
        return verdict == "rekey" or self.risk_type == "svg_icon"

    @staticmethod
    def _widget_script_url(data: dict[str, Any]) -> Union[str, None]:
        """URL of the widget script that carries the signing key."""
        static_path = data.get("static_path")
        if not static_path:
            return None
        return asset_url(str(static_path).rstrip("/") + "/js/gcaptcha4.js")

    def _recover_key(self, script: Union[str, None]) -> int:
        """Forget the cached modulus and recover it from a widget script."""
        keyring.reset()
        if not script:
            raise GeeTestSolveFailed(
                "GeeTest response has no widget script to recover the signing key from"
            )
        try:
            return keyring.remember(keyring.extract_modulus(script))
        except (LookupError, ValueError) as exc:
            raise GeeTestSolveFailed(
                f"could not recover the GeeTest signing key: {exc}"
            ) from exc

    def _build_fields(
        self, data: dict[str, Any], fields: dict[str, Any], modulus: int
    ) -> str:
        """Sign one answer variant."""
        lot = data["lot_number"]
        payload: dict[str, Any] = {}
        payload |= pow_module.solve_from_detail(
            data["pow_detail"], self.captcha_id, lot
        )
        payload |= fields
        payload["lot_number"] = lot
        return crypto.sign(payload, str(data.get("pt", "1")), modulus)

    def _trials(
        self,
        data: dict[str, Any],
        images: dict[str, bytes],
        svg: Union[str, None],
    ) -> list[dict[str, Any]]:
        """The candidate payloads for the loaded lot, in submission order."""
        if self.risk_type == "svg_icon":
            if svg is None:
                raise GeeTestSolveFailed("svg_icon challenge has no question SVG")
            return svg_icon.trials(svg)
        return [
            answers.fields(self.risk_type, data, images, self.voice_model_path)
        ]


class GeeTestV4Solver(_V4Core):
    """Synchronous GeeTest V4 solver."""

    def _get_text(self, client: httpx.Client, url: str) -> str:
        return request(client, url).text

    def _get_bytes(self, client: httpx.Client, url: str) -> bytes:
        return request(client, url).content

    def _fetch_images(
        self, client: httpx.Client, data: dict[str, Any]
    ) -> dict[str, bytes]:
        if self.risk_type == "slide":
            require_data(data, "bg", "slice", "ypos")
            return {
                key: self._get_bytes(client, asset_url(data[key]))
                for key in ("bg", "slice")
            }
        if self.risk_type == "voice":
            require_data(data, "voice_path")
            return {"voice": self._get_bytes(client, asset_url(data["voice_path"]))}
        return {}

    def _load(self, client: httpx.Client) -> dict[str, Any]:
        callback = callback_name()
        url = load_url(self.captcha_id, self.risk_type, self.lang, callback)
        return self._parse_load(self._get_jsonp(client, url, callback))

    def _load_auto(self, client: httpx.Client) -> dict[str, Any]:
        callback = callback_name()
        url = load_url(self.captcha_id, None, self.lang, callback)
        return self._parse_auto(self._get_jsonp(client, url, callback))

    def _get_jsonp(
        self, client: httpx.Client, url: str, callback: str
    ) -> dict[str, Any]:
        return unwrap(self._get_text(client, url), callback)

    def _verify(
        self, client: httpx.Client, data: dict[str, Any], w: str
    ) -> dict[str, Any]:
        callback = callback_name()
        url = verify_url(
            self.captcha_id,
            self.risk_type,
            data["lot_number"],
            str(data["payload"]),
            str(data["process_token"]),
            w,
            callback,
        )
        return self._get_jsonp(client, url, callback)

    def _script_text(self, client: httpx.Client, url: str) -> str:
        """The widget script at ``url``, read once per solver instance."""
        if url not in self._script_cache:
            self._script_cache[url] = self._get_text(client, url)
        return self._script_cache[url]

    def _signing_key(self, client: httpx.Client, data: dict[str, Any]) -> int:
        """The modulus to sign with, recovering it once per process."""
        if keyring.recovered():
            return keyring.current()
        return self._refresh_key(client, data)

    def _refresh_key(self, client: httpx.Client, data: dict[str, Any]) -> int:
        url = self._widget_script_url(data)
        script = self._script_text(client, url) if url else None
        return self._recover_key(script)

    def _answer(
        self, method: str, client: httpx.Client, data: dict[str, Any]
    ) -> dict[str, Any]:
        if method == "voice" and self.risk_type != "voice":
            return self._voice_fallback(client)

        svg = None
        if self.risk_type == "svg_icon":
            require_data(data, "question_path")
            svg = self._get_text(client, asset_url(str(data["question_path"])))
        images = self._fetch_images(client, data)
        trials = self._trials(data, images, svg)

        for sweep in range(_SWEEPS):
            verdict = "rejected"
            for fields in trials:
                w = self._build_fields(data, fields, keyring.current())
                response = self._verify(client, data, w)
                verdict = self._verdict(response)
                if verdict == "success":
                    return response
                if verdict == "rekey":
                    break
            if not self._should_recover(verdict, sweep):
                return {}
            self._refresh_key(client, data)
        return {}

    def _voice_fallback(self, client: httpx.Client) -> dict[str, Any]:
        original = self.risk_type
        self.risk_type = "voice"
        try:
            data = self._load(client)
            if not data.get("voice_path"):
                return {}
            self._signing_key(client, data)
            audio = self._fetch_images(client, data)["voice"]
            fields = answers.voice.answer_fields(audio, self.voice_model_path)
            self._refresh_key(client, data)
            response = self._verify(
                client, data, self._build_fields(data, fields, keyring.current())
            )
        finally:
            self.risk_type = original
        return response if self._verdict(response) == "success" else {}

    def _solve_once(self, client: httpx.Client) -> dict[str, Any]:
        data = (
            self._load_auto(client)
            if self.requested_risk_type == "auto"
            else self._load(client)
        )
        self._signing_key(client, data)

        for method in ANSWER_ORDER[self.risk_type]:
            response = self._answer(method, client, data)
            if response:
                return self._seccode(response)
        raise GeeTestSolveFailed(
            f"every answer strategy for {self.risk_type!r} was rejected"
        )

    def solve(self, attempts: int = 3) -> dict[str, Any]:
        """Solve a challenge and return the server's ``seccode`` object.

        The returned dict carries ``captcha_id``, ``lot_number``,
        ``pass_token``, ``gen_time`` and ``captcha_output`` — exactly what the
        widget submits back to the target site.
        """
        last: Union[Exception, None] = None
        with httpx.Client(**self._client_kwargs()) as client:
            for attempt in range(attempts):
                try:
                    return self._solve_once(client)
                except (GeeTestError, RequestFailed) as exc:
                    last = exc
                    if attempt == attempts - 1:
                        raise
                    time.sleep(0.5 + random.random() * 0.5)
        raise GeeTestSolveFailed(f"exhausted attempts: {last}")  # pragma: no cover


__all__ = ["GeeTestV4Solver", "SUPPORTED_RISK_TYPES"]
