# reCAPTCHA V3

**reCAPTCHA V3** is a score-based risk analysis CAPTCHA from Google. Unlike V2, it runs silently in the background without user interaction.

PyPasser supports two modes for reCAPTCHA V3:

1. **Pure HTTP Mode (Recommended)**: Solves reCAPTCHA V3 entirely over HTTP requests using an anchor URL. Fast, lightweight, and requires **no browser**.
2. **Page Mode**: Attaches to an active Playwright page and waits for `#g-recaptcha-response` to populate in the DOM.

Supports both **Standard** (`/api2/anchor`) and **Enterprise** (`/enterprise/anchor`) endpoints.

---

## Quick Example (Pure HTTP)

```python
from pypasser.captcha import recaptcha

result = recaptcha.v3.solve(
    anchor_url="https://www.google.com/recaptcha/api2/anchor?ar=1&k=6LdyC2cUAAAAACGuDK2VJzwkaoq2M9vg2qW6yO0u&co=aHR0cHM6Ly8yY2FwdGNoYS5jb206NDQz&hl=en&v=1&size=invisible&cb=123"
)

if result.is_solved:
    token = result.response_token
    print("g-recaptcha-response token:", token)
```

---

## How to Get the Anchor URL

In your browser developer tools:

1. Open the **Network** tab.
2. Filter requests by `anchor`.
3. Locate the URL starting with `https://www.google.com/recaptcha/api2/anchor` (or `/enterprise/anchor`).
4. Copy the entire URL including all query parameters (`k`, `co`, `v`, `size`, etc.).

---

## API Reference

### `solve()`
```python
def solve(
    first: Any = None,
    *,
    anchor_url: Optional[str] = None,
    page: Any = None,
    proxy: Optional[str] = None,
    timeout: Union[int, float] = 20,
) -> SolverResult: ...
```

### `asolve()`
```python
async def asolve(
    first: Any = None,
    *,
    anchor_url: Optional[str] = None,
    page: Any = None,
    proxy: Optional[str] = None,
    timeout: Union[int, float] = 20,
) -> SolverResult: ...
```

#### Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `first` | `Any` | `None` | Convenience positional parameter. If a `str`, treated as `anchor_url`. If an object, treated as `page`. |
| `anchor_url` | `str \| None` | `None` | Full anchor URL copied from the reCAPTCHA iframe `src`. |
| `page` | `Page \| None` | `None` | Playwright or Patchright `Page` object displaying the site. |
| `proxy` | `str \| None` | `None` | Proxy URL string (`http://`, `socks5://`). Only applies in HTTP mode. |
| `timeout` | `int \| float` | `20` | HTTP request timeout in seconds (HTTP mode) or DOM token polling timeout (Page mode). |

#### Return Value
Returns a [`SolverResult`](../api/structs.md) where:

- `is_solved`: `True` if a token was obtained.
- `response_token`: String containing the `g-recaptcha-response` token.

---

## Dynamic Render Version Syncing

Google periodically updates its client-side JavaScript bundles (`api.js`, `enterprise.js`), which changes the internal render version query parameter (`v`). If a solver hardcodes an old version, Google assigns the token a lower risk score or rejects it.

PyPasser automatically fetches Google's active render version and caches it for 1 hour:

```python
from pypasser.captcha.recaptcha.v3.render import latest_render_version, alatest_render_version

# Fetches and caches the current Google v parameter (e.g., '1P_fl286-9...'):
v = latest_render_version("https://www.google.com/recaptcha/api.js")
```

---

## Page Mode Example (Playwright)

If the target site triggers reCAPTCHA V3 dynamically upon form submission, use Page mode:

```python
from patchright.sync_api import sync_playwright
from pypasser.captcha import recaptcha

with sync_playwright() as pw:
    browser = pw.chromium.launch()
    page = browser.new_page()
    page.goto("https://2captcha.com/demo/recaptcha-v3")

    # Pass the Page object to extract the token directly from the DOM:
    result = recaptcha.v3.solve(page=page, timeout=15)
    print("Extracted token:", result.response_token)

    browser.close()
```

---

## Exceptions

| Exception | Cause |
|---|---|
| `InvalidAnchorURL` | Anchor URL missing required `k` (site key) or `co` (origin hash) parameters, or both `anchor_url` and `page` were omitted. |
| `RecaptchaTokenNotFound` | Anchor response did not contain the hidden initial `recaptcha-token`. |
| `RecaptchaResponseNotFound` | Reload call did not return `rresp`, or Page mode timed out waiting for DOM element. |
| `RequestFailed` | Network or HTTP transport error. |
