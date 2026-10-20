"""GeeTest V4 protocol constants.

The RSA modulus is not shipped: it rotates, so the solver recovers the live
value from the widget script at runtime (see ``keyring``).
"""

from __future__ import annotations

# Same API behind two hostnames, so requests rotate to the next host
# on rate-limit responses.
BASES = (
    "https://gcaptcha4.geevisit.com",
    "https://gcaptcha4.geetest.com",
)

STATIC_BASE = "https://static.geetest.com"
REFERER = "https://gt4.geetest.com/"

DEFAULT_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

DEFAULT_LANG = "eng"

RSA_EXPONENT = 0x10001

# Shape of the obfuscation key call site in the widget script.
JS_KEY_PATTERN = r'\}\}\("(.+?)"\)\}'
MODULUS_MIN_HEX = 200
