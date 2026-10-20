from __future__ import annotations

from typing import Any, Union
from urllib.parse import urlparse

from pypasser.exceptions import InvalidProxyURL

SUPPORTED_SCHEMES = {"http", "https", "socks4", "socks4a", "socks5", "socks5h"}


def normalize_proxy_url(proxy: str) -> str:
    """Validate and normalize a proxy URL string for httpx.

    Maps ``socks5h://`` to ``socks5://`` since ``socksio`` handles DNS
    resolution at the proxy.

    Raises
    ------
    InvalidProxyURL
        If the scheme is unsupported, host is missing, or the URL cannot be parsed.
    """
    if not isinstance(proxy, str) or not proxy.strip():
        raise InvalidProxyURL("Proxy must be a non-empty URL string.")

    try:
        parsed = urlparse(proxy.strip())
    except Exception as exc:  # pragma: no cover
        raise InvalidProxyURL(f"Malformed proxy URL: {proxy!r}") from exc

    scheme = (parsed.scheme or "").lower()
    if scheme not in SUPPORTED_SCHEMES:
        raise InvalidProxyURL(
            f"Unsupported proxy scheme {scheme!r}. Expected one of {sorted(SUPPORTED_SCHEMES)}."
        )

    if not parsed.hostname:
        raise InvalidProxyURL(f"Proxy URL is missing host: {proxy!r}")

    if scheme == "socks5h":
        scheme = "socks5"

    return f"{scheme}://{parsed.netloc}{parsed.path}"


def build_httpx_mounts(proxy: str | None) -> dict[str, Any] | None:
    """Build an httpx ``mounts`` dict routing all traffic through ``proxy``."""
    if proxy is None:
        return None

    import httpx

    if isinstance(proxy, str):
        return {"all://": httpx.HTTPTransport(proxy=normalize_proxy_url(proxy))}

    raise InvalidProxyURL(f"Expected a proxy URL string, got {type(proxy).__name__}")


def httpx_client_kwargs(
    timeout: Union[int, float],
    headers: dict[str, str] | None = None,
    proxy: str | None = None,
) -> dict[str, Any]:
    """Keyword arguments for an ``httpx.Client``/``AsyncClient``."""
    kwargs: dict[str, Any] = {"timeout": timeout}
    if headers is not None:
        kwargs["headers"] = headers
    mounts = build_httpx_mounts(proxy)
    if mounts is not None:
        kwargs["mounts"] = mounts
    return kwargs
