"""Lemin cropped captcha (HTTP-only)


Where the two values come from
------------------------------
CAPTCHA_ID
    The page loads a script whose URL ends in ``/js``:

        https://api.leminnow.com/captcha/v1/cropped/CROPPED_3dfdd5c_.../js

    The ``CROPPED_...`` segment is the captcha id.

DOMAIN
    The site's origin (scheme + host, no path) — e.g.
    ``https://example.com``. It must match the origin the widget runs on;
    send it without a trailing slash.
"""

from pypasser.captcha import lemin
from pypasser.exceptions import LeminError

CAPTCHA_ID = "CROPPED_3dfdd5c_d1872b526b794d83ba3b365eb15a200b"
DOMAIN = "https://2captcha.com"
PROXY = None  # e.g. "http://user:pass@host:port" or "socks5://host:port"
ATTEMPTS = 3

try:
    result = lemin.solve(CAPTCHA_ID, domain=DOMAIN, proxy=PROXY, attempts=ATTEMPTS)
    print("solved:", result.is_solved, "\ntokens:\n", result.response_token)
except LeminError as exc:
    raise SystemExit(f"could not solve: {exc}") from exc

