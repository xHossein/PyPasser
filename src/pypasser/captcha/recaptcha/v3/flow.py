"""Engine-agnostic reCaptcha V3 HTTP flow (anchor URL -> token).

The flow is HTTP only: it walks the two Google endpoints the widget's own
JavaScript walks (``anchor`` for the request token, ``reload`` for the
reCaptcha token).
"""

from __future__ import annotations

import re
from typing import Union

import httpx

from pypasser.captcha.recaptcha.v3.anchor import ParsedAnchor, parse_anchor_url
from pypasser.captcha.recaptcha.v3.constants import (
    BASE_HEADERS,
    BASE_URL,
    POST_DATA,
)
from pypasser.captcha.recaptcha.v3.render import latest_render_version
from pypasser.exceptions import RecaptchaResponseNotFound, RecaptchaTokenNotFound, RequestFailed
from pypasser.structs import SolverResult

_TOKEN_RE = re.compile(r'"recaptcha-token" value="(.*?)"')
_RESP_RE = re.compile(r'"rresp","(.*?)"')

_DEFAULT_TIMEOUT = 20


def _client_kwargs(proxy: str | None, timeout: Union[int, float]) -> dict:
    from pypasser.proxies import build_httpx_mounts

    mounts = build_httpx_mounts(proxy)
    if mounts is not None:
        return {"headers": BASE_HEADERS, "timeout": timeout, "mounts": mounts}
    return {"headers": BASE_HEADERS, "timeout": timeout}


class _V3Core:
    """Core HTTP steps, independent of sync/async transport."""

    def __init__(
        self,
        anchor_url: str,
        proxy: str | None = None,
        timeout: Union[int, float] = _DEFAULT_TIMEOUT,
    ) -> None:
        self.parsed: ParsedAnchor = parse_anchor_url(anchor_url)
        params = self.parsed.params
        self.v = params.get("v", "")
        self.k = params.get("k", "")
        self.co = params.get("co", "")
        self.proxy = proxy
        self.timeout = timeout

    def _anchor_params(self) -> dict[str, str]:
        params = dict(self.parsed.params)
        if self.v:
            params["v"] = self.v
        return params

    def _token_url(self) -> str:
        return BASE_URL.format(f"{self.parsed.endpoint}/anchor")

    def _reload_url(self) -> str:
        return BASE_URL.format(f"{self.parsed.endpoint}/reload")

    def _post_data(self, token: str) -> str:
        return POST_DATA.format(self.v, token, self.k, self.co)

    def _extract_token(self, text: str) -> str:
        match = _TOKEN_RE.search(text)
        if not match:
            raise RecaptchaTokenNotFound()
        return match.group(1)

    def _extract_response(self, text: str) -> str:
        match = _RESP_RE.search(text)
        if not match:
            raise RecaptchaResponseNotFound()
        return match.group(1)


def _wrap_request_error(exc: Exception) -> RequestFailed:
    return RequestFailed(f"Request to Google failed: {exc}")


class V3Solver(_V3Core):
    """Synchronous reCaptcha V3 bypass (HTTP only)."""

    def solve(self) -> SolverResult:
        with httpx.Client(**_client_kwargs(self.proxy, self.timeout)) as client:
            return self._run(client)

    def _run(self, client: httpx.Client) -> SolverResult:
        self.v = latest_render_version(client=client, endpoint=self.parsed.endpoint) or self.v

        try:
            anchor_resp = client.get(self._token_url(), params=self._anchor_params())
        except httpx.RequestError as exc:
            raise _wrap_request_error(exc) from exc

        token = self._extract_token(anchor_resp.text)

        try:
            reload_resp = client.post(
                self._reload_url(), content=self._post_data(token), params=f"k={self.k}"
            )
        except httpx.RequestError as exc:
            raise _wrap_request_error(exc) from exc

        return SolverResult(is_solved=True, response_token=self._extract_response(reload_resp.text))
