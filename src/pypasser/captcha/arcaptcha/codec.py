"""Binary codec (``ob``/``db``) used by the ARCaptcha HTTP API."""

from __future__ import annotations

import json
import secrets
from typing import Any

_F_INIT = 90


def _rol8(value: int, n: int) -> int:
    return ((value << n) | (value >> (8 - n))) & 0xFF


def _ror8(value: int, n: int) -> int:
    return ((value >> n) | (value << (8 - n))) & 0xFF


def ob_encode(obj: Any) -> bytes:
    """Encode a JSON-serializable object into the obfuscated wire format."""
    payload = json.dumps(obj, separators=(",", ":")).encode("utf-8")
    s, c, u, v = secrets.token_bytes(4)
    out = bytearray((s, c, u, v))
    f = _F_INIT

    def step(t: int) -> None:
        nonlocal s, c, u, v, f
        s = (s + c) & 0xFF
        c = (c ^ u) & 0xFF
        u = (u + v) & 0xFF
        v = (v ^ s) & 0xFF
        e = ((t ^ ((s + v) & 0xFF)) + f) & 0xFF
        r = _rol8(e, 3)
        out.append(r)
        f = r

    for b in payload:
        step(b)
    pad_len = secrets.randbelow(16)
    for _ in range(pad_len):
        step(secrets.randbelow(256))
    step(pad_len)
    return bytes(out)


def db_decode(data: bytes) -> Any:
    """Decode the obfuscated wire format back into a Python object."""
    if len(data) < 5:
        raise ValueError("payload too short")
    s, c, u, v = data[0], data[1], data[2], data[3]
    f = _F_INIT
    out = bytearray()
    for byte in data[4:]:
        s = (s + c) & 0xFF
        c = (c ^ u) & 0xFF
        u = (u + v) & 0xFF
        v = (v ^ s) & 0xFF
        e = (_ror8(byte, 3) - f) & 0xFF
        e ^= (s + v) & 0xFF
        out.append(e)
        f = byte
    pad_len = out[-1]
    payload = bytes(out[: len(out) - 1 - pad_len])
    return json.loads(payload.decode("utf-8"))
