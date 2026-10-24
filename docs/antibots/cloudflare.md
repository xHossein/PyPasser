# Cloudflare Interstitial

**Cloudflare** protects websites with a full-page interstitial screen ("Just a moment...", 5-second challenge). When a browser passes this check, Cloudflare sets a session cookie named **`cf_clearance`**.

PyPasser's Cloudflare module automates this challenge page, clicks the verification checkbox if present, waits for the redirect, and extracts the `cf_clearance` cookie alongside the exact `User-Agent`.

---

## Installation Requirement

Cloudflare's bot heuristics detect standard headless automation flags. We strongly recommend **Patchright** or **Camoufox**:

```bash
pip install "PyPasser[stealth]"
patchright install chromium
```

---

## Quick Example (Headed Browser + HTTP Replay)

```python
import httpx
from patchright.sync_api import sync_playwright
from pypasser.antibot import cloudflare

target_url = "https://steamdb.info/"

# Step 1: Clear the Cloudflare interstitial using a headed stealth browser
with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto(target_url)

    result = cloudflare.solve(page, timeout=60)
    browser.close()

if not result.is_solved or not result.cookies.get("cf_clearance"):
    raise RuntimeError("Failed to clear Cloudflare wall")

print("Successfully cleared Cloudflare!")
print("cf_clearance:", result.cookies["cf_clearance"][:20], "...")

# Step 2: Replay the session over plain HTTP from the same IP:
headers = {"User-Agent": result.user_agent}
with httpx.Client(cookies=result.cookies, headers=headers) as client:
    response = client.get(target_url)
    print("Replay status:", response.status_code)
    print("Page title:", response.text[:80])
```

---

## Async Example

```python
import asyncio
import httpx
from patchright.async_api import async_playwright
from pypasser.antibot import cloudflare

async def main():
    target_url = "https://steamdb.info/"

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto(target_url)

        result = await cloudflare.asolve(page, timeout=60)
        await browser.close()

    if result.is_solved:
        async with httpx.AsyncClient(
            cookies=result.cookies,
            headers={"User-Agent": result.user_agent}
        ) as client:
            resp = await client.get(target_url)
            print("Async HTTP replay status:", resp.status_code)

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
    timeout: Union[int, float] = 60.0,
) -> SolverResult: ...
```

### `asolve()`
```python
async def asolve(
    page: Any,
    backend: str = "auto",
    attempts: int = 3,
    timeout: Union[int, float] = 60.0,
) -> SolverResult: ...
```

#### Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `page` | `Page` | *Required* | Playwright or Patchright `Page` on the challenge page ("Just a moment..."). |
| `backend` | `str` | `"auto"` | Browser automation backend: `"auto"`, `"playwright"`, or `"patchright"`. |
| `attempts` | `int` | `3` | Maximum checkbox click attempts if the challenge re-renders. |
| `timeout` | `int \| float` | `60.0` | Total seconds to wait for clearance and page redirect. |

#### Return Value
Returns a [`SolverResult`](../api/structs.md) where:

- `is_solved`: `True` when the challenge is successfully cleared and `cf_clearance` is acquired.
- `cookies`: Dictionary of active cookies containing `{"cf_clearance": "..."}`.
- `user_agent`: String containing the browser's `navigator.userAgent`.
- `response_token`: String containing Turnstile response token if one was issued.

---

## Important Rules for Cloudflare Clearance

1. **Headed Browser Recommended**: Cloudflare's TLS fingerprinting, canvas noise checks, and CDP detection will block headless Chrome on high-security zones.
2. **IP Matching**: You **must** perform your subsequent HTTP requests from the exact same egress IP that ran the browser session.
3. **User-Agent Matching**: Always pass `headers={"User-Agent": result.user_agent}` on every request. Cloudflare checks that the User-Agent header matches the one hashed into `cf_clearance`.

---

## Exceptions

| Exception | Cause |
|---|---|
| `CloudflareClearanceError` | Challenge appeared to pass but no `cf_clearance` cookie was set (IP soft-block or adapter cookie extraction failure). |
| `CloudflareError` | Base exception for Cloudflare clearance issues. |
| `UnknownBackend` | Could not determine the browser adapter type from `page`. |
| `BackendNotAsync` | Attempted `asolve()` using a synchronous Playwright page instance. |
