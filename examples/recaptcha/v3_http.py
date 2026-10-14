"""reCAPTCHA V3 over pure HTTP — no browser once you hold the anchor URL.

    python examples/recaptcha/v3_http.py [ANCHOR_URL]

Requires: pip install PyPasser

V3 never renders anything a browser must solve: the anchor URL is the only
page-derived artifact, and it carries the fresh session token (``ar``) Google
requires. Paste one below — read it off the ``src`` of the ``iframe[title=
'reCAPTCHA']`` on any page that renders the widget (or mine one live with
``examples/recaptcha/v3.py``), then every solve is plain HTTP:

    recaptcha.v3.solve(anchor_url) -> SolverResult(response_token="...")

Anchors MAY die within minutes. If a site keeps
expiring yours, mine a fresh anchor per run with v3.py's page mode.

Submit the token as ``g-recaptcha-response`` with your request.
"""

import sys

from pypasser.captcha import recaptcha

# A fresh anchor URL read off the target site's reCAPTCHA iframe:
#   https://www.google.com/recaptcha/api2/anchor?ar=...&k=...&co=...&hl=...
ANCHOR_URL = "PASTE_A_FRESH_ANCHOR_URL_HERE"

anchor_url = sys.argv[1] if len(sys.argv) > 1 else ANCHOR_URL
if "PASTE_A_FRESH" in anchor_url:
    raise SystemExit(__doc__)

result = recaptcha.v3.solve(anchor_url)

print("solved:", result.is_solved)
print("token:", result.response_token)
