"""HTTP transport for the GeeTest V4 endpoints."""

from __future__ import annotations

import json
import random
import time
import urllib.parse
import uuid
from typing import Any, Union

import httpx

from pypasser.captcha.geetest.v4.protocol.constants import (
    BASES,
    REFERER,
    STATIC_BASE,
)
from pypasser.exceptions import GeeTestError, RequestFailed, RequestRateLimited

_RATE_LIMIT_STATUSES = (429,)


def _shed(resp: Any) -> bool:
    """Whether this mirror failed to serve the request (try the next one)."""
    return resp.status_code in _RATE_LIMIT_STATUSES or resp.status_code >= 500


_preferred = 0
"""Host that last answered; survives the rest of the process's requests."""


def _mirror_path(url: str) -> Union[str, None]:
    """The path to re-request from another mirror, or ``None`` for assets."""
    base = next((b for b in BASES if url.startswith(b)), None)
    return None if base is None else url[len(base):]


def _check_status(resp: Any, url: str) -> None:
    """Raise :class:`RequestFailed` on an HTTP error response."""
    try:
        resp.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise RequestFailed(
            f"GeeTest request failed with HTTP {resp.status_code}: {url}"
        ) from exc


def request(client: Any, url: str) -> Any:
    """GET ``url``, rotating to the next mirror when a host fails to serve it."""
    global _preferred
    path = _mirror_path(url)
    if path is None:
        try:
            resp = client.get(url, headers=headers())
        except httpx.TransportError as exc:
            raise RequestFailed(f"GeeTest asset request failed: {url}") from exc
        _check_status(resp, url)
        return resp

    for index in _host_order():
        try:
            resp = client.get(BASES[index] + path, headers=headers())
        except httpx.TransportError:
            continue
        if not _shed(resp):
            _check_status(resp, url)
            _preferred = index
            return resp
    raise RequestRateLimited(f"no GeeTest host served the request: {url}")


async def arequest(client: Any, url: str) -> Any:
    """Async :func:`request` — same host rotation on failure."""
    global _preferred
    path = _mirror_path(url)
    if path is None:
        try:
            resp = await client.get(url, headers=headers())
        except httpx.TransportError as exc:
            raise RequestFailed(f"GeeTest asset request failed: {url}") from exc
        _check_status(resp, url)
        return resp

    for index in _host_order():
        try:
            resp = await client.get(BASES[index] + path, headers=headers())
        except httpx.TransportError:
            continue
        if not _shed(resp):
            _check_status(resp, url)
            _preferred = index
            return resp
    raise RequestRateLimited(f"no GeeTest host served the request: {url}")


def _host_order() -> list[int]:
    """Preferred host first, then the rest."""
    return [_preferred] + [i for i in range(len(BASES)) if i != _preferred]


def callback_name() -> str:
    """A fresh JSONP callback name (the widget's generated shape)."""
    return f"geetest_{int(random.random() * 10000) + int(time.time() * 1000)}"


def parse_jsonp(body: str, callback: str) -> dict[str, Any]:
    """Strip ``callback(...)`` and decode the inner JSON."""
    marker = callback + "("
    start = body.find(marker)
    if start == -1:
        raise RequestFailed(f"GeeTest response is not JSONP for {callback!r}")
    payload = body[start + len(marker):]
    end = payload.rfind(")")
    if end == -1:
        raise RequestFailed("GeeTest JSONP response is unterminated")
    try:
        return json.loads(payload[:end])
    except ValueError as exc:
        raise RequestFailed(f"GeeTest JSONP body is not valid JSON: {exc}") from exc


def unwrap(body: str, callback: str) -> dict[str, Any]:
    """Return the JSONP envelope itself."""
    outer = parse_jsonp(body, callback)
    if not isinstance(outer, dict):
        raise RequestFailed(f"GeeTest response is not an object: {body[:200]}")
    data = outer.get("data")
    return data if isinstance(data, dict) else outer


def client_kwargs(
    proxy: Union[str, None], timeout: Union[int, float], user_agent: str
) -> dict[str, Any]:
    """Keyword arguments for an httpx client (shared by sync and async)."""
    kwargs: dict[str, Any] = {"timeout": timeout, "headers": {"User-Agent": user_agent}}
    if proxy:
        from pypasser.proxies import build_httpx_mounts

        mounts = build_httpx_mounts(proxy)
        if mounts is not None:
            kwargs["mounts"] = mounts
    return kwargs


def base_params(callback: str, captcha_id: str, **extra: Any) -> dict[str, Any]:
    """Common query parameters every endpoint expects."""
    return {"callback": callback, "captcha_id": captcha_id, **extra}


def load_url(
    captcha_id: str, risk_type: Union[str, None], lang: str, callback: str
) -> str:
    """Build a ``/load`` URL.

    ``risk_type=None`` omits the parameter, which lets the server pick the
    type it has configured for the captcha id.
    """
    params = base_params(
        callback,
        captcha_id,
        challenge=str(uuid.uuid4()),
        client_type="web",
        lang=lang,
    )
    if risk_type is not None:
        params["risk_type"] = risk_type
    return f"{BASES[0]}/load?{urllib.parse.urlencode(params)}"


def verify_url(
    captcha_id: str,
    risk_type: str,
    lot_number: str,
    payload: str,
    process_token: str,
    w: str,
    callback: str,
) -> str:
    """Build a ``/verify`` URL."""
    params = base_params(
        callback,
        captcha_id,
        client_type="web",
        lot_number=lot_number,
        risk_type=risk_type,
        payload=payload,
        process_token=process_token,
        payload_protocol="1",
        pt="1",
        w=w,
    )
    return f"{BASES[0]}/verify?{urllib.parse.urlencode(params)}"


def asset_url(path: str) -> str:
    """Absolute URL for a static asset path from a ``/load`` response."""
    if path.startswith("http"):
        return path
    return f"{STATIC_BASE}/{path.lstrip('/')}"


def require_data(data: dict[str, Any], *fields: str) -> None:
    """Raise if the response lacks a field or carries an empty one.

    ``ypos`` is a row index and ``0`` is a valid value, so presence is checked
    against ``None``/``""`` rather than truthiness.
    """
    missing = [f for f in fields if data.get(f) in (None, "")]
    if missing:
        raise GeeTestError(f"GeeTest response missing {', '.join(missing)}: {data}")


def headers() -> dict[str, str]:
    return {"Referer": REFERER, "Accept": "*/*", "Accept-Encoding": "identity"}
