"""GeeTest V4 signing envelope.

The verify payload travels as ``w``::

    w = hex(AES_CBC(key=uid, iv=0)  PKCS7(json))  ||  hex(RSA_PKCS1v15(uid))

``uid`` is a random 16-hex-digit string invented per request; it is the AES
key, and the RSA blob carries it back to the server. A plaintext payload
(``pt=0``) is rejected by the server, so the envelope is not optional.
"""

from __future__ import annotations

import json
import random
from typing import Any

from pypasser.captcha.geetest.v4.protocol.constants import RSA_EXPONENT

_ZERO_IV = b"0000000000000000"


def random_uid() -> str:
    """A random 16-character hex string, used as the per-request AES key."""
    return "".join(f"{random.randint(0, 0xFFFF):04x}" for _ in range(4))


def _aes_cbc(key: str, plaintext: str) -> bytes:
    from cryptography.hazmat.primitives import padding as sym_padding
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

    padder = sym_padding.PKCS7(128).padder()
    data = padder.update(plaintext.encode()) + padder.finalize()
    encryptor = Cipher(algorithms.AES(key.encode()), modes.CBC(_ZERO_IV)).encryptor()
    return encryptor.update(data) + encryptor.finalize()


def _rsa_encrypt_uid(uid: str, modulus: int) -> str:
    from cryptography.hazmat.primitives.asymmetric import padding, rsa

    public_key = rsa.RSAPublicNumbers(RSA_EXPONENT, modulus).public_key()
    return public_key.encrypt(uid.encode(), padding.PKCS1v15()).hex()


def sign(payload: dict[str, Any], pt: str, modulus: int) -> str:
    """Return the ``w`` value for ``payload``.

    Parameters
    ----------
    payload: dict
        The JSON body to sign.
    pt: str
        The server's ``pt`` flag from ``/load``. ``"0"`` means the server
        accepts a plaintext body (never observed in practice, but harmless
        to honour). The body is returned as raw JSON; the URL builder applies
        the percent-encoding exactly once.
    modulus: int
        The RSA public modulus to encrypt the AES key with.
    """
    raw = json.dumps(payload, separators=(",", ":"))
    if not pt or pt == "0":
        return raw
    uid = random_uid()
    return _aes_cbc(uid, raw).hex() + _rsa_encrypt_uid(uid, modulus)
