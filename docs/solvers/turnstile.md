# Cloudflare Turnstile

**Cloudflare Turnstile** is Cloudflare's smart CAPTCHA alternative. It runs non-interactive checks in the background or presents an interactive checkbox widget.

PyPasser automates Turnstile widgets by locating the embedded iframe, clicking the checkbox with natural delays, and waiting for the token to be issued into the DOM.

---

## Installation Requirement

Turnstile requires a browser automation engine. For best stealth performance against Cloudflare's bot heuristics, we strongly recommend **Patchright**:

```bash
pip install "PyPasser[stealth]"
patchright install chromium
```

---

## Quick Example (Sync)

```python
from patchright.sync_api import sync_playwright
from pypasser.captcha import turnstile

with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto("https://2captcha.com/demo/cloudflare-turnstile")

    # Solves Turnstile on the page
    result = turnstile.solve(page)

    if result.is_solved:
        print("Turnstile token:", result.response_token)
        # Form can now be submitted
        page.locator("button[type='submit']").click()

    browser.close()
```

---

## Quick Example (Async)

```python
import asyncio
from patchright.async_api import async_playwright
from pypasser.captcha import turnstile

async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto("https://2captcha.com/demo/cloudflare-turnstile")

        result = await turnstile.asolve(page)
        if result.is_solved:
            print("Turnstile token:", result.response_token)

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
    attempts: int = 3,
    timeout: float = 30,
) -> SolverResult: ...
```

### `asolve()`
```python
async def asolve(
    page: Any,
    backend: str = "auto",
    attempts: int = 3,
    timeout: float = 30,
) -> SolverResult: ...
```

#### Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `page` | `Page` | *Required* | Playwright or Patchright `Page` object displaying the Turnstile challenge. |
| `backend` | `str` | `"auto"` | Browser automation backend: `"auto"`, `"playwright"`, or `"patchright"`. |
| `attempts` | `int` | `3` | Maximum number of checkbox click attempts if the widget re-renders. |
| `timeout` | `float` | `30` | Maximum polling duration in seconds to wait for widget completion. |

#### Return Value
Returns a [`SolverResult`](../api/structs.md) where:

- `is_solved`: `True` when the token is ready.
- `response_token`: String containing the `cf-turnstile-response` token read from `input[name="cf-turnstile-response"]`.
- `cookies`: If solving a standalone challenge page, includes the active cookies.
- `user_agent`: User-Agent string of the browser context.

---

## Headless vs Headed Modes

Cloudflare actively fingerpaints headless browsers. When running in a headless environment:

- **Standard Playwright headless** (`headless=True`) is frequently blocked or fails to pass Turnstile.
- **Patchright** or **Camoufox** can pass Turnstile headlessly on clean IP addresses.
- If you encounter recurring failures, launch the browser with `headless=False`.

---

## Exceptions

| Exception | Cause |
|---|---|
| `UnknownBackend` | Could not determine the browser adapter type from `page`. |
| `BackendNotAsync` | Attempted `asolve()` using a synchronous Playwright page instance. |
