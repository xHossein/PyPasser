"""reCAPTCHA V3 Enterprise — same HTTP bypass, enterprise anchor
(/enterprise/anchor) and site key.

    python examples/recaptcha/v3_enterprise.py

Requires: pip install PyPasser
"""

from patchright.sync_api import sync_playwright

from pypasser.captcha import recaptcha

_ANCHOR_JS = """() => new Promise(resolve => {
    const poll = setInterval(() => {
        const frame = document.querySelector('iframe[title="reCAPTCHA"]');
        if (frame && frame.src.includes('anchor?')) {
            clearInterval(poll);
            resolve(frame.src);
        }
    }, 100);
    setTimeout(() => { clearInterval(poll); resolve(''); }, 15000);
})"""

with sync_playwright() as p:
    page = p.chromium.launch(headless=False).new_page()
    page.goto("https://2captcha.com/demo/recaptcha-v3-enterprise")

    anchor = page.evaluate(_ANCHOR_JS)
    print("anchor:", anchor[:80], "...")

    result = recaptcha.v3.solve(anchor)

    print("solved:", result.is_solved)
    if result.is_solved:
        print("token:", result.response_token)
