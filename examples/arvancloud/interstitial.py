"""ArvanCloud interstitial — browserless: the challenge page hides the
``__arcsjs`` / ``__arcsjsc`` cookie values in a JSFuck ``values()`` function,
decoded in pure Python and replayed over HTTP.

    python examples/arvancloud/interstitial.py

Requires: pip install PyPasser  (no browser, no extras)

The cookies are bound to the IP and User-Agent; the replay must send
``result.user_agent`` from the same address.
"""

import httpx

from pypasser.antibot import arvancloud
from pypasser.antibot.arvancloud.challenge import is_challenge

URL = "https://esale.ikco.ir/"

result = arvancloud.solve(URL)

print("solved:", result.is_solved)
print("cookies:", result.cookies)

headers = {"User-Agent": result.user_agent} if result.user_agent else {}
with httpx.Client(
    cookies=result.cookies, headers=headers, timeout=30, follow_redirects=True
) as client:
    response = client.get(URL)
    challenged = is_challenge(response.text)
    print(f"replay: {response.status_code} {'CHALLENGED' if challenged else 'OK'}")
