"""Wire protocol for the Lemin cropped captcha.

The three HTTP calls the widget makes — fetch the image, download the scene,
pre-validate the answer — are shared by the sync and async solvers. 
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import io
import time
import uuid
from dataclasses import dataclass
from typing import Any, Optional

import httpx

from pypasser.captcha.lemin.constants import (
    API_BASE,
    BASE_PIECE,
    ENC,
    PIECE_MARGIN,
    SECRET,
    VERSION,
)
from pypasser.exceptions import LeminSolveFailed, RequestFailed

DEFAULT_SCREEN = (1920, 1080)


@dataclass(frozen=True)
class Challenge:
    """One cropped challenge, decoded from the image endpoint."""

    challenge_id: str
    image: Any  # numpy array, kept untyped so vision decides the dtype
    pieces: int = 1
    piece_size: int = BASE_PIECE
    margin: int = PIECE_MARGIN
    caption: str = ""


def parse_layout(raw: str) -> tuple[Optional[tuple[int, int, int]], str]:
    """Split the base64 ``pieces,base,margin`` override, if present."""
    try:
        decoded = base64.b64decode(raw).decode("ascii")
        pieces, base, margin = (int(part) for part in decoded.split(","))
        return (pieces, base, margin), decoded
    except (binascii.Error, UnicodeDecodeError, ValueError):
        return None, ""


def parse_image(raw: bytes) -> Any:
    """Decode raw image bytes to a numpy RGBA array."""
    import numpy as np
    from PIL import Image

    return np.asarray(Image.open(io.BytesIO(raw)).convert("RGBA"))


def image_url(
    captcha_id: str,
    domain: str,
    challenge_id: str,
    screen: tuple[int, int] = DEFAULT_SCREEN,
) -> str:
    """Signed scene URL for *challenge_id*."""
    utc_offset = -int(time.timezone / 3600 * 60)
    query = (
        f"screen_width={screen[0]}&screen_height={screen[1]}"
        f"&utc_offset={utc_offset}&v={VERSION}&domain={domain}&enc={ENC}"
    )
    url = f"{API_BASE}/{captcha_id}/image/{challenge_id}?{query}"
    sign = hashlib.md5((url + SECRET).encode()).hexdigest()
    return f"{url}&lsign={sign}"


def decode_challenge(challenge_id: str, body: str, image: Any) -> Challenge:
    """Decode the image endpoint's ``url|caption[|layout]`` body."""
    parts = body.split("|")
    layout = None
    if len(parts) > 2:
        layout, _ = parse_layout(parts[2])
    caption = parts[1] if len(parts) > 1 else ""
    if layout:
        pieces, base, margin = layout
    else:
        pieces, base, margin = 1, BASE_PIECE, PIECE_MARGIN
    return Challenge(
        challenge_id=challenge_id,
        image=image,
        pieces=max(1, pieces),
        piece_size=base,
        margin=margin,
        caption=caption,
    )


def parse_verify(payload: Any) -> str:
    """Pull the pv_token out of a pre-validate reply or raise."""
    if not isinstance(payload, dict):
        raise LeminSolveFailed(f"unexpected pre-validate body: {payload!r}")
    if payload.get("success"):
        data = payload.get("data") or {}
        token = data.get("pv_token")
        if not token:
            raise LeminSolveFailed("pre-validate succeeded without a pv_token")
        return str(token)
    code = payload.get("code") or payload.get("message") or "unknown error"
    raise LeminSolveFailed(f"answer rejected: {code}")


def check_image_response(response: httpx.Response) -> str:
    """Validate the image endpoint's reply and return its body."""
    if response.status_code == 403:
        raise RequestFailed(
            "Lemin refused the image request (403): the captcha id or domain "
            "does not match, or the widget secret changed"
        )
    if response.status_code == 429:
        raise RequestFailed("Lemin rate limited the image request (429)")
    response.raise_for_status()
    body = response.text
    if "|" not in body:
        raise LeminSolveFailed(f"unexpected image response: {body[:120]!r}")
    return body


def check_verify_response(response: httpx.Response) -> Any:
    """Validate the pre-validate reply and return its JSON body."""
    if response.status_code >= 500:
        raise RequestFailed(f"Lemin pre-validate failed: HTTP {response.status_code}")
    try:
        return response.json()
    except ValueError as exc:
        raise RequestFailed(
            f"Lemin pre-validate returned a non-JSON body: {response.text[:120]!r}"
        ) from exc


def new_challenge_id() -> str:
    return str(uuid.uuid4())


def pre_validate_url() -> str:
    """Endpoint that checks an answer and hands back the pv_token."""
    return f"{API_BASE}/pre-validate"


__all__ = [
    "Challenge",
    "DEFAULT_SCREEN",
    "check_image_response",
    "check_verify_response",
    "decode_challenge",
    "image_url",
    "new_challenge_id",
    "parse_image",
    "parse_layout",
    "parse_verify",
    "pre_validate_url",
]
