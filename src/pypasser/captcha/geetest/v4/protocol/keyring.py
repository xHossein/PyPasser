"""Runtime recovery of the GeeTest V4 RSA public modulus.

The modulus rotates, so it is recovered from the widget
script the server itself points at (``static_path`` + ``js``).

The script hides its string table behind two layers:

1. one long ``decodeURI("...")`` literal holding percent-escaped bytes;
2. those bytes are XORed against a key that appears as the argument of a
   ``}}\\(...)\\)}`` call site.

XORing them back yields a flat table of ``^``-separated tokens, one of which
is the modulus as a long hex string.
"""

from __future__ import annotations

import re
import urllib.parse
from typing import Optional

from pypasser.captcha.geetest.v4.protocol.constants import (
    JS_KEY_PATTERN,
    MODULUS_MIN_HEX,
)
from pypasser.exceptions import GeeTestSolveFailed

_DECODE_RE = re.compile(r'decodeURI\("((?:[^"\\]|\\.)*)"\)')
_KEY_RE = re.compile(JS_KEY_PATTERN)
_HEX_RE = re.compile(r"[0-9A-Fa-f]{%d,}" % MODULUS_MIN_HEX)

_cached_modulus: Optional[int] = None


def _deobfuscate(script: str) -> str:
    """Undo the decodeURI + XOR layers and return the flat token table."""
    blobs = _DECODE_RE.findall(script)
    keys = _KEY_RE.findall(script)
    if not blobs or not keys:
        raise LookupError("widget script has no obfuscated table or key")

    raw = urllib.parse.unquote(blobs[0]).encode("latin1", "replace")
    key = keys[0].encode("latin1", "replace")
    if not key:
        raise LookupError("widget script carries an empty obfuscation key")
    return bytes(b ^ key[i % len(key)] for i, b in enumerate(raw)).decode("latin1")


def extract_modulus(script: str) -> int:
    """Recover the RSA modulus from the raw widget script text."""
    candidates = _HEX_RE.findall(_deobfuscate(script))
    if not candidates:
        raise LookupError("modulus not present in the deobfuscated table")
    return int(max(candidates, key=len), 16)


def remember(modulus: int) -> int:
    """Cache a recovered modulus for subsequent signatures."""
    global _cached_modulus
    _cached_modulus = modulus
    return modulus


def recovered() -> bool:
    """Whether a modulus has been recovered this process."""
    return _cached_modulus is not None


def current() -> int:
    """The recovered modulus; raises if none has been recovered yet."""
    if _cached_modulus is None:
        raise GeeTestSolveFailed(
            "GeeTest signing key has not been recovered from the widget script"
        )
    return _cached_modulus


def reset() -> None:
    """Forget the cached modulus (used when the server rejects a signature)."""
    global _cached_modulus
    _cached_modulus = None


__all__ = ["current", "extract_modulus", "recovered", "remember", "reset"]
