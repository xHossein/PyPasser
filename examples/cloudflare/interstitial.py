"""Cloudflare interstitial — clear the full-page "Just a moment..." wall and
replay the session over plain HTTP.

    python examples/cloudflare/interstitial.py

Requires: pip install PyPasser[stealth] && patchright install chromium

Headless is not an option for this row (FAIL in Headless mode).

The interstitial's challenge IS the Turnstile widget, so the browser pass is
shared with the widget solver; ``antibot.cloudflare`` adds the clearance
contract — the result must carry the ``cf_clearance`` cookie (or it raises
``CloudflareClearanceError``). The cookie is bound to the User-Agent and IP,
so the replay must send ``result.user_agent`` from the same address.
"""

import httpx
from patchright.sync_api import sync_playwright

from pypasser.antibot import cloudflare

URL = "https://steamdb.info"

with sync_playwright() as p:
    page = p.chromium.launch(headless=False).new_page()
    page.goto(URL)

    result = cloudflare.solve(page, timeout=60)

print("solved:", result.is_solved)
clearance = (result.cookies or {}).get("cf_clearance")
if clearance:
    print("cf_clearance:", clearance[:40], "...")
else:
    print("cf_clearance: none — the page was already clear; replay decides")

headers = {"User-Agent": result.user_agent} if result.user_agent else {}
with httpx.Client(
    cookies=result.cookies, headers=headers, timeout=30, follow_redirects=True
) as client:
    response = client.get(URL)
    blocked = response.status_code in (403, 503) or "just a moment" in response.text.lower()
    print(f"replay: {response.status_code} — {'BLOCKED' if blocked else 'OK'}")
