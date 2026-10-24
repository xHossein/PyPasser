# Lemin Cropped CAPTCHA

**Lemin Cropped CAPTCHA** is an interactive jigsaw puzzle challenge where users drag one or more cutout puzzle pieces into matching empty slots on a background scene.

PyPasser solves Lemin Cropped challenges in **a few seconds over pure HTTP** without opening a browser or rendering JavaScript.

---

## How PyPasser Solves Lemin (Pure HTTP)

The entire Lemin solving flow consists of three lightweight HTTP requests:

1. **Fetch Challenge URL**: Calls `GET https://api.leminnow.com/captcha/v1/cropped/{captcha_id}/image/{challenge_id}` signed with an MD5 widget signature (`lsign`). The response yields the scene image URL and layout metadata (`url|caption|layout`).
2. **Local Computer Vision**: Downloads the raw PNG scene and uses Canny edge detection and template correlation to locate the exact pixel coordinates of the cutout slot.
3. **Trajectory Generation & Pre-Validation**: Synthesizes a natural, human-like mouse drag trajectory with micro-jitter, encodes the path in base32, and calls `POST https://api.leminnow.com/captcha/v1/cropped/pre-validate` to obtain a valid `pv_token`.

---

## Installation Requirement

Lemin requires the `[vision]` extra for image processing and edge detection:

```bash
pip install "PyPasser[vision]"
```

---

## Quick Example (Sync)

```python
from pypasser.captcha import lemin

result = lemin.solve(
    captcha_id="CROPPED_3dfdd5c_d1872b526b794d83ba3b365eb15a200b",
    domain="https://2captcha.com",
)

if result.is_solved:
    data = result.response_token
    print("Pre-validation Token:", data["pv_token"])
    print("Answer Trajectory:", data["answer"][:30], "...")
    print("Challenge ID:", data["challenge_id"])
```

---

## Quick Example (Async)

```python
import asyncio
from pypasser.captcha import lemin

async def main():
    result = await lemin.asolve(
        captcha_id="CROPPED_3dfdd5c_d1872b526b794d83ba3b365eb15a200b",
        domain="https://2captcha.com",
    )
    if result.is_solved:
        print("Async Token:", result.response_token["pv_token"])

asyncio.run(main())
```

---

## API Reference

### `solve()`
```python
def solve(
    captcha_id: str,
    *,
    domain: str,
    proxy: Union[str, None] = None,
    timeout: Union[int, float] = 20,
    user_agent: str = DEFAULT_UA,
    screen: tuple[int, int] = (1920, 1080),
    attempts: int = 3,
    jitter: float = 3.0,
) -> SolverResult: ...
```

### `asolve()`
```python
async def asolve(
    captcha_id: str,
    *,
    domain: str,
    proxy: Union[str, None] = None,
    timeout: Union[int, float] = 20,
    user_agent: str = DEFAULT_UA,
    screen: tuple[int, int] = (1920, 1080),
    attempts: int = 3,
    jitter: float = 3.0,
) -> SolverResult: ...
```

#### Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `captcha_id` | `str` | *Required* | Target Lemin captcha ID, formatted as `CROPPED_<hash>`. |
| `domain` | `str` | *Required* | The origin where the widget is embedded (e.g., `"https://example.com"`). Must match registered domain. |
| `proxy` | `str \| None` | `None` | Proxy URL string (`http://`, `socks5://`). |
| `timeout` | `int \| float` | `20` | HTTP request timeout in seconds. |
| `user_agent` | `str` | `DEFAULT_UA` | Browser User-Agent header sent with requests. |
| `screen` | `tuple[int, int]` | `(1920, 1080)` | Virtual screen resolution `(width, height)` reported to Lemin API. |
| `attempts` | `int` | `3` | Maximum number of fresh challenge attempts. |
| `jitter` | `float` | `3.0` | Random pixel displacement applied to points along the simulated drag path. |

#### Return Value
Returns a [`SolverResult`](../api/structs.md) where:

- `is_solved`: `True` when pre-validation succeeds.
- `response_token`: A dictionary containing three strings:
  ```python
  {
      "pv_token": "gAAAAABq2c39...",      # Token submitted to backend verify API
      "answer": "0x12c..._?_0x14e...",     # Encoded mouse drag path
      "challenge_id": "9b1deb4d-3b7d..."   # Challenge UUID
  }
  ```

---

## Browser Automation Injection

When automating a web page with Playwright or Selenium, you do not need to let the browser drag the puzzle piece. Instead, solve headlessly with PyPasser and inject the tokens into Lemin's hidden form inputs:

### Playwright Injection Example

```python
from patchright.sync_api import sync_playwright
from pypasser.captcha import lemin

with sync_playwright() as pw:
    browser = pw.chromium.launch()
    page = browser.new_page()
    page.goto("https://2captcha.com/demo/lemin")

    # 1. Solve headlessly via HTTP
    result = lemin.solve(
        captcha_id="CROPPED_3dfdd5c_d1872b526b794d83ba3b365eb15a200b",
        domain="https://2captcha.com",
    )

    data = result.response_token

    # 2. Inject answer and challenge_id into hidden inputs
    page.evaluate(
        """({ answer, challenge_id }) => {
            const elAns = document.querySelector('input[name="lemin_answer"]') ||
                          document.querySelector('#LCanswer');
            const elCid = document.querySelector('input[name="lemin_challenge_id"]') ||
                          document.querySelector('#LCchallenge_id');
            if (elAns) elAns.value = answer;
            if (elCid) elCid.value = challenge_id;
        }""",
        {"answer": data["answer"], "challenge_id": data["challenge_id"]},
    )

    # 3. Submit form or trigger verify button
    page.locator("button[type='submit']").click()
    browser.close()
```

---

## Exceptions

| Exception | Cause |
|---|---|
| `LeminError` | Base exception for all Lemin solving errors. |
| `LeminSolveFailed` | Puzzle cutout could not be identified by CV, pre-validation was rejected, or multi-piece challenge requested. |
| `RequestFailed` | Network transport error or image download failure. |
