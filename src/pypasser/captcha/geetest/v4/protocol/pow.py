"""GeeTest V4 proof-of-work.

Each ``/load`` response carries a ``pow_detail`` describing a hash puzzle. The
answer is a random suffix whose digest of ``prefix + suffix`` has at least
``bits`` leading zero bits::

    prefix = f"{version}|{bits}|{hashfunc}|{datetime}|{captcha_id}|{lot_number}||"

The server checks the returned ``pow_msg`` (prefix + suffix) and ``pow_sign``
(its digest), so both must be echoed back.
"""

from __future__ import annotations

import hashlib
from typing import Any, Callable

from pypasser.captcha.geetest.v4.protocol.crypto import random_uid
from pypasser.exceptions import GeeTestError, GeeTestSolveFailed

_HASHES: dict[str, Callable[..., Any]] = {
    "md5": hashlib.md5,
    "sha1": hashlib.sha1,
    "sha256": hashlib.sha256,
}

# When ``bits`` is not a multiple of 4 the last partial hex digit only needs
# its high bits clear: ``bits % 4`` leftover bits cap the digit's value.
_PARTIAL_MAX = {1: "7", 2: "3", 3: "1"}


def prefix(
    version: str,
    bits: int,
    hashfunc: str,
    datetime: str,
    captcha_id: str,
    lot_number: str,
) -> str:
    """The fixed part of the PoW message, shared by every candidate suffix."""
    return f"{version}|{bits}|{hashfunc}|{datetime}|{captcha_id}|{lot_number}||"


def hash_meets_bits(digest_hex: str, bits: int) -> bool:
    """Whether ``digest_hex`` has at least ``bits`` leading zero bits."""
    whole, extra = divmod(bits, 4)
    if not digest_hex.startswith("0" * whole):
        return False
    if extra == 0:
        return True
    return digest_hex[whole] <= _PARTIAL_MAX[extra]


def solve_pow(
    prefix_str: str,
    hashfunc: str,
    bits: int,
    max_attempts: int = 1 << 24,
) -> tuple[str, str]:
    """Brute-force a suffix; return ``(pow_msg, pow_sign)``."""
    algo = _HASHES.get(hashfunc)
    if algo is None:
        raise GeeTestError(f"unsupported pow hashfunc {hashfunc!r}")
    for _ in range(max_attempts):
        suffix = random_uid()
        digest = algo((prefix_str + suffix).encode()).hexdigest()
        if hash_meets_bits(digest, bits):
            return prefix_str + suffix, digest
    raise GeeTestSolveFailed(f"pow not solved after {max_attempts} attempts")


def solve_from_detail(
    detail: dict[str, Any], captcha_id: str, lot_number: str
) -> dict[str, str]:
    """Build the ``pow_msg``/``pow_sign`` pair from a ``pow_detail`` block."""
    bits = int(detail["bits"])
    hashfunc = str(detail["hashfunc"])
    prefix_str = prefix(
        str(detail["version"]),
        bits,
        hashfunc,
        str(detail["datetime"]),
        captcha_id,
        lot_number,
    )
    msg, sign = solve_pow(prefix_str, hashfunc, bits)
    return {"pow_msg": msg, "pow_sign": sign}
