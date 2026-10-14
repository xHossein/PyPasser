"""reCAPTCHA V2 invisible — the widget has no checkbox; the challenge opens
after the page's own action.

    python examples/recaptcha/v2_invisible.py

Requires: pip install "PyPasser[stealth,speech]" && patchright install chromium

Clicking the demo's Check button executes the widget, which opens the challenge
popup PyPasser then solves (audio fallback via vosk).
"""

from patchright.sync_api import sync_playwright

from pypasser.captcha import recaptcha

with sync_playwright() as p:
    page = p.chromium.launch(headless=False).new_page()
    page.goto("https://2captcha.com/demo/recaptcha-v2-invisible")

    page.get_by_role("button", name="Check").first.click()  # opens the challenge
    result = recaptcha.v2.solve(page)

    print("solved:", result.is_solved)
    if result.is_solved:
        print("token:", result.response_token)
