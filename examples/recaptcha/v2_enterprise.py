"""reCAPTCHA V2 Enterprise — same widget flow, site key with different gpgl
behavior; the solver handles it unchanged.

    python examples/recaptcha/v2_enterprise.py

Requires: pip install "PyPasser[stealth,speech]" && patchright install chromium
"""

from patchright.sync_api import sync_playwright

from pypasser.captcha import recaptcha

with sync_playwright() as p:
    page = p.chromium.launch(headless=False).new_page()
    page.goto("https://2captcha.com/demo/recaptcha-v2-enterprise")

    result = recaptcha.v2.solve(page)

    print("solved:", result.is_solved)
    if result.is_solved:
        print("token:", result.response_token)
        page.get_by_role("button", name="Check").first.click()  # demo verifies it
