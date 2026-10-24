# Quickstart

PyPasser provides a consistent API across every solver:

- **Sync**: `solve(...)`
- **Async**: `asolve(...)`
- **Result**: Always returns a [`SolverResult`](../api/structs.md)

---

## 1. Pure HTTP Solvers (Zero Browser)

Pure HTTP solvers execute in a few seconds without launching any browser instance or Node.js runtime.

### Lemin Cropped CAPTCHA

```python
from pypasser.captcha import lemin

result = lemin.solve(
    captcha_id="CROPPED_3dfdd5c_d1872b526b794d83ba3b365eb15a200b",
    domain="https://2captcha.com",
)

if result.is_solved:
    # Lemin returns pre-validation tokens in response_token dict:
    pv_token = result.response_token["pv_token"]
    answer = result.response_token["answer"]
    challenge_id = result.response_token["challenge_id"]
    print("Pre-validation token:", pv_token)
```

### GeeTest V4 (Auto-detect)

```python
import asyncio
from pypasser.captcha import geetest

async def main():
    # Asynchronous solve with automatic challenge type detection
    result = await geetest.v4.asolve(
        captcha_id="54088bb07d2df3c46b79f80300b0abbe",
        risk_type="auto",
    )
    if result.is_solved:
        print("GeeTest seccode:", result.response_token)

asyncio.run(main())
```

---

## 2. Browser Automation Solvers

For widgets that require a browser context, pass a Playwright or Patchright `Page` object.

### Cloudflare Turnstile

```python
from patchright.sync_api import sync_playwright
from pypasser.captcha import turnstile

with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto("https://2captcha.com/demo/cloudflare-turnstile")

    # Solves embedded or popup Turnstile widget
    result = turnstile.solve(page)

    if result.is_solved:
        print("Turnstile token:", result.response_token)
        # Form submission can proceed
        page.locator("button[type='submit']").click()

    browser.close()
```

### reCAPTCHA V2 (Audio Bypass)

```python
from patchright.sync_api import sync_playwright
from pypasser.captcha import recaptcha

with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto("https://2captcha.com/demo/recaptcha-v2")

    # Automates checkbox click, audio download, and local Vosk transcription
    result = recaptcha.v2.solve(page)

    if result.is_solved:
        print("reCAPTCHA V2 token:", result.response_token)

    browser.close()
```

---

## 3. Anti-Bot Clearance & HTTP Session Replay

Anti-bot modules clear interstitial walls ("Just a moment...", JS challenges) and return session cookies bound to the solver's `User-Agent`. You then replay these cookies over standard HTTP clients like `httpx` or `requests`.

```python
import httpx
from patchright.sync_api import sync_playwright
from pypasser.antibot import cloudflare

target_url = "https://steamdb.info/"

with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto(target_url)

    # Solve Cloudflare 5s interstitial wall
    result = cloudflare.solve(page)
    browser.close()

if result.is_solved:
    # Replay session cookies over plain HTTP from the same IP:
    headers = {"User-Agent": result.user_agent}
    with httpx.Client(cookies=result.cookies, headers=headers) as client:
        response = client.get(target_url)
        print("Status code:", response.status_code)
        print("Page title:", response.text[:100])
```

---

## 4. Error Handling Pattern

Catch base `PyPasserError` or specific module exceptions:

```python
from pypasser.exceptions import (
    PyPasserError,
    LeminSolveFailed,
    GeeTestSolveFailed,
    IpBlock,
)

try:
    result = lemin.solve(...)
except LeminSolveFailed as e:
    print(f"Lemin challenge could not be solved: {e}")
except PyPasserError as e:
    print(f"General PyPasser error: {e}")
```
