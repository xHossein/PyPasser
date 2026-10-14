"""reCAPTCHA V2 callback — the site verifies the token itself via a JS callback
(no Check button to click; the demo page reacts on its own).

    python examples/recaptcha/v2_callback.py

Requires: pip install "PyPasser[stealth,speech]" && patchright install chromium
"""

from patchright.sync_api import sync_playwright

from pypasser.captcha import recaptcha

with sync_playwright() as p:
    page = p.chromium.launch(headless=False).new_page()
    page.goto("https://2captcha.com/demo/recaptcha-v2-callback")

    result = recaptcha.v2.solve(page)

    print("solved:", result.is_solved)
    if result.is_solved:
        print("token:", result.response_token)
