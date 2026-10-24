# reCAPTCHA V2

**reCAPTCHA V2** is Google's interactive challenge presenting either a checkbox ("I'm not a robot") or image tile grids.

PyPasser solves reCAPTCHA V2 challenges using an **offline audio recognition pipeline**:

1. Clicks the "I'm not a robot" checkbox iframe.
2. If an image challenge appears, clicks the **audio challenge button** (headphone icon).
3. Downloads the audio challenge clip (`.mp3`).
4. Converts audio to PCM using `imageio-ffmpeg` / `pydub`.
5. Transcribes the spoken digits locally with **Vosk** (offline speech recognition).
6. Enters the text into the answer box and verifies.

Supports **Checkbox**, **Invisible**, **Callback**, and **Enterprise** variants.

---

## Installation Requirement

V2 audio solving requires browser automation and speech packages:

```bash
pip install "PyPasser[stealth,speech]"
patchright install chromium
```

---

## Quick Example (Sync)

```python
from patchright.sync_api import sync_playwright
from pypasser.captcha import recaptcha

with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto("https://2captcha.com/demo/recaptcha-v2")

    # Solve the challenge on the current page
    result = recaptcha.v2.solve(page)

    if result.is_solved:
        print("Success! Token:", result.response_token)
        # Token is already populated in document.querySelector('#g-recaptcha-response')
        page.locator("button[type='submit']").click()

    browser.close()
```

---

## Quick Example (Async)

```python
import asyncio
from patchright.async_api import async_playwright
from pypasser.captcha import recaptcha

async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto("https://2captcha.com/demo/recaptcha-v2")

        result = await recaptcha.v2.asolve(page)
        if result.is_solved:
            print("Token:", result.response_token)

        await browser.close()

asyncio.run(main())
```

---

## API Reference

### `solve()`
```python
def solve(
    page: Any,
    backend: str = "auto",
    play: bool = True,
    attempts: int = 3,
    timeout: float = 10,
) -> SolverResult: ...
```

### `asolve()`
```python
async def asolve(
    page: Any,
    backend: str = "auto",
    play: bool = True,
    attempts: int = 3,
    timeout: float = 10,
) -> SolverResult: ...
```

#### Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `page` | `Page` | *Required* | Playwright or Patchright `Page` displaying the reCAPTCHA V2 challenge. |
| `backend` | `str` | `"auto"` | Browser automation backend: `"auto"`, `"playwright"`, or `"patchright"`. |
| `play` | `bool` | `True` | Whether to click the audio play button before fetching the download link. |
| `attempts` | `int` | `3` | Maximum number of audio transcription retries. |
| `timeout` | `float` | `10` | Per-element wait timeout in seconds. |

#### Return Value
Returns a [`SolverResult`](../api/structs.md) where:

- `is_solved`: `True` when the green checkmark is confirmed and the token is ready.
- `response_token`: String containing the `g-recaptcha-response` value.

---

## Handling reCAPTCHA V2 Variants

### Invisible reCAPTCHA
Invisible reCAPTCHA has no initial checkbox. It triggers on button click or form submit. First trigger the challenge, then call `solve()`:

```python
# Click the form submit button that invokes grecaptcha.execute()
page.locator("#submit-button").click()

# PyPasser detects and solves the popup challenge frame
result = recaptcha.v2.solve(page)
```

### Callback reCAPTCHA
When reCAPTCHA defines a data-callback function, PyPasser automatically calls the callback after solving so client-side listeners execute properly.

---

## Bot Detection & IP Blocks

Google actively monitors IP reputation on audio challenge endpoints. If an IP is flagged, Google shows:
> *"Your computer or network may be sending automated queries. To protect our users, we can't process your request right now."*

When this occurs, PyPasser raises `pypasser.exceptions.IpBlock`.

### How to avoid IP blocks:

1. **Use Patchright**: Always use `patchright` instead of standard `playwright` (`pip install "PyPasser[stealth]"`).
2. **High-Reputation Residential Proxies**: Data center IPs are frequently pre-flagged by Google.
3. **Headful mode**: Headed browsers have substantially lower block rates than headless browsers.

---

## Exceptions

| Exception | Cause |
|---|---|
| `IpBlock` | Google blocked the IP address from requesting audio challenges. |
| `RecaptchaResponseNotFound` | Audio download link could not be located, or response token missing. |
| `AudioDecodeError` | Challenge audio could not be decoded to PCM format. |
| `UnknownBackend` | Could not determine the browser adapter type from `page`. |
| `BackendNotAsync` | Attempted `asolve()` with a synchronous Playwright page instance. |
