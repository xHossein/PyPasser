"""Cloudflare Turnstile widget — solve the checkbox on a normal page
(the 2captcha demo uses Cloudflare's invisible test site key).

    python examples/cloudflare/turnstile.py

Requires: pip install PyPasser[stealth] && patchright install chromium

Cloudflare's widget platform scores plain Playwright as automation and never
renders the widget for it — the demo only passes on a stealth engine.
"""

from patchright.sync_api import sync_playwright

from pypasser.captcha import turnstile

with sync_playwright() as p:
    page = p.chromium.launch(headless=False).new_page()
    page.goto("https://2captcha.com/demo/cloudflare-turnstile")

    result = turnstile.solve(page)

    print("solved:", result.is_solved)
    if result.is_solved:
        print("token:", result.response_token)
        page.get_by_role("button", name="Check").first.click()  # demo verifies it
