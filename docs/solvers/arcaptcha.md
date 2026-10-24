# ARCaptcha

**ARCaptcha** (`arcaptcha.ir` / `arcaptcha.co`) is the primary CAPTCHA provider used across Iranian websites, government services, banks, and e-commerce platforms.

PyPasser provides full support for ARCaptcha across all challenge types using **pure HTTP** and **browser automation modes**:

- **Puzzle Slider**: Solved headlessly via local computer vision contour alignment.
- **9-Grid Question**: Automatically falls back to the Persian voice challenge.
- **Voice Challenge**: Transcribed locally using an offline Persian Vosk ASR model.
- **Instant Challenges**: Clears `cookie` and `accept` challenge types without user interaction.

---

## Installation Requirement

ARCaptcha utilizes computer vision for slider puzzles and speech recognition for Persian voice challenges:

```bash
pip install "PyPasser[vision,speech]"
```

---

## Quick Example (Pure HTTP)

```python
from pypasser.captcha import arcaptcha

# Pure HTTP solve without opening a browser
result = arcaptcha.solve(
    site_key="d6ggpvy684",
    domain="demo.arcaptcha.co",
)

if result.is_solved:
    print("arcaptcha-token:", result.response_token)
```

---

## Quick Example (Page Mode with Playwright)

If you are already driving a browser session with Playwright, pass the `page` instance:

```python
from patchright.sync_api import sync_playwright
from pypasser.captcha import arcaptcha

with sync_playwright() as pw:
    browser = pw.chromium.launch()
    page = browser.new_page()
    page.goto("https://demo.arcaptcha.co/")

    # Solves the widget and populates the hidden input[name='arcaptcha-token']
    result = arcaptcha.solve(page=page)

    if result.is_solved:
        print("Token:", result.response_token)
        page.locator("#submit-btn").click()

    browser.close()
```

---

## API Reference

### `solve()`
```python
def solve(
    first: Any = None,
    *,
    site_key: Optional[str] = None,
    domain: Optional[str] = None,
    page: Any = None,
    proxy: Optional[str] = None,
    timeout: Union[int, float] = 20,
    lang: str = "fa",
    voice_model: Union[str, None] = None,
    attempts: int = 3,
    token_wait: Union[int, float] = 5,
) -> SolverResult: ...
```

### `asolve()`
```python
async def asolve(
    first: Any = None,
    *,
    site_key: Optional[str] = None,
    domain: Optional[str] = None,
    page: Any = None,
    proxy: Optional[str] = None,
    timeout: Union[int, float] = 20,
    lang: str = "fa",
    voice_model: Union[str, None] = None,
    attempts: int = 3,
    token_wait: Union[int, float] = 5,
) -> SolverResult: ...
```

#### Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `first` | `Any` | `None` | Convenience positional parameter. If a `str`, treated as `site_key`. If an object, treated as `page`. |
| `site_key` | `str \| None` | `None` | Target site's ARCaptcha public key. |
| `domain` | `str \| None` | `None` | Origin the widget is registered for (e.g., `"example.ir"`). |
| `page` | `Page \| None` | `None` | Playwright `Page` displaying the ARCaptcha widget. |
| `proxy` | `str \| None` | `None` | Proxy URL string (`http://`, `socks5://`). |
| `timeout` | `int \| float` | `20` | HTTP request timeout in seconds. |
| `lang` | `str` | `"fa"` | Language code sent to ARCaptcha API. |
| `voice_model` | `str \| None` | `None` | Custom path to local Persian Vosk model. Auto-downloads `vosk-model-fa-0.5` if omitted. |
| `attempts` | `int` | `3` | Maximum number of fresh challenge attempts. |
| `token_wait` | `int \| float` | `5` | Seconds to wait for page's own widget token before initiating solver (Page mode). |

#### Return Value
Returns a [`SolverResult`](../api/structs.md) where:

- `is_solved`: `True` when verification succeeds.
- `response_token`: String containing the `challenge_id` token submitted as `arcaptcha-token`.

---

## Exceptions

| Exception | Cause |
|---|---|
| `ARCaptchaError` | Base exception, or missing required `site_key` / `domain`. |
| `ARCaptchaBlocked` | ARCaptcha server flagged/blocked the session (`captcha_type == "block"`). |
| `ARCaptchaSolveFailed` | Could not solve the challenge within the attempt budget. |
| `RequestFailed` | Network or HTTP error communicating with ARCaptcha servers. |
