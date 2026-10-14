"""reCAPTCHA V2 — solve the checkbox on the 2captcha demo page.

    python examples/recaptcha/v2.py

Requires: pip install "PyPasser[stealth,speech]" && patchright install chromium

The solve clicks the checkbox; if Google serves the audio challenge it is
transcribed with vosk (the small English model downloads on first use, ~40 MB).
"""

from patchright.sync_api import sync_playwright

from pypasser.captcha import recaptcha

with sync_playwright() as p:
    page = p.chromium.launch(headless=False).new_page()
    page.goto("https://2captcha.com/demo/recaptcha-v2")

    result = recaptcha.v2.solve(page)

    print("solved:", result.is_solved)
    if result.is_solved:
        print("token:", result.response_token)
        page.get_by_role("button", name="Check").first.click()  # demo verifies it
