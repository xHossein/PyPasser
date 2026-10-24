# GeeTest V4

**GeeTest V4** is an enterprise-grade CAPTCHA suite featuring multiple interactive challenges and behavioral risk analysis.

PyPasser provides a **100% pure HTTP** solver for the complete GeeTest V4 family. It communicates directly with GeeTest's `/load` and `/verify` endpoints, performs client-side RSA/AES cryptography, and computes proof-of-work (PoW) locally without any browser overhead.

---

## Supported Risk Types

GeeTest V4 assigns challenges based on risk scoring (`risk_type`):

| `risk_type` | Challenge Description | Solving Strategy |
|---|---|---|
| `"auto"` | **Auto-detects** challenge type configured on the server | Queries `/load` and dispatches appropriate solver |
| `"slide"` | Classic jigsaw puzzle slider | Computer vision edge alignment + natural mouse trajectory |
| `"ai"` | Behavioral pass-through | Instant PoW clearance |
| `"winlinze"` | 2-point or 3-point connector trail | Natural cursor curve synthesis |
| `"match"` | Icon/symbol pair matching | Template correlation |
| `"nine"` | 9-grid image recognition | Automatic voice fallback via Vosk ASR |
| `"icon"` | Symbol / object recognition | Automatic voice fallback via Vosk ASR |
| `"svg_icon"` | Vector graphic rotation/alignment | Keyframe sweep + voice fallback |
| `"voice"` | Spoken digit audio challenge | Headless offline speech recognition via Vosk |

---

## Installation Requirement

GeeTest V4 uses computer vision for puzzle matching and speech recognition for voice fallback:

```bash
pip install "PyPasser[vision,speech]"
```

---

## Quick Example (Auto-Detect)

```python
from pypasser.captcha import geetest

# Pure HTTP solve in a few seconds:
result = geetest.v4.solve(
    captcha_id="54088bb07d2df3c46b79f80300b0abbe",
    risk_type="auto",
)

if result.is_solved:
    # response_token is a JSON string containing the seccode dictionary
    import json
    seccode = json.loads(result.response_token)
    print("Pass Token:", seccode["pass_token"])
    print("Captcha Output:", seccode["captcha_output"])
    print("Lot Number:", seccode["lot_number"])
```

---

## API Reference

### `solve()`
```python
def solve(
    captcha_id: str,
    *,
    risk_type: str = "auto",
    proxy: Optional[str] = None,
    timeout: Union[int, float] = 20,
    lang: str = "eng",
    user_agent: str = DEFAULT_UA,
    attempts: int = 3,
    voice_model_path: Optional[str] = None,
) -> SolverResult: ...
```

### `asolve()`
```python
async def asolve(
    captcha_id: str,
    *,
    risk_type: str = "auto",
    proxy: Optional[str] = None,
    timeout: Union[int, float] = 20,
    lang: str = "eng",
    user_agent: str = DEFAULT_UA,
    attempts: int = 3,
    voice_model_path: Optional[str] = None,
) -> SolverResult: ...
```

#### Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `captcha_id` | `str` | *Required* | Target site's 32-character GeeTest V4 captcha ID. |
| `risk_type` | `str` | `"auto"` | Target risk type: `"auto"`, `"slide"`, `"ai"`, `"winlinze"`, `"match"`, `"nine"`, `"icon"`, `"svg_icon"`, `"voice"`. |
| `proxy` | `str \| None` | `None` | Proxy URL string (`http://`, `socks5://`). |
| `timeout` | `int \| float` | `20` | HTTP request timeout in seconds. |
| `lang` | `str` | `"eng"` | Language code sent to GeeTest endpoints. |
| `user_agent` | `str` | `DEFAULT_UA` | Browser User-Agent string sent with requests. |
| `attempts` | `int` | `3` | Maximum number of fresh challenge attempts. |
| `voice_model_path` | `str \| None` | `None` | Custom path to local Vosk speech model directory. |

#### Return Value
Returns a [`SolverResult`](../api/structs.md) where:

- `is_solved`: `True` when verification succeeds.
- `response_token`: A JSON string representing the GeeTest validation payload:
  ```json
  {
    "captcha_id": "54088bb07d2df3c46b79f80300b0abbe",
    "lot_number": "060c49ff96a1438fa747fc32d8ec11f7",
    "pass_token": "8ea81a5c0e0b6...",
    "gen_time": "1729600000",
    "captcha_output": "P7F4mK..."
  }
  ```

---

## Browser Automation Integration

To validate a form protected by GeeTest V4 in Playwright or Selenium, inject the `seccode` object or submit it to the site's backend verification API:

```python
import json
from pypasser.captcha import geetest

# 1. Solve headlessly via PyPasser HTTP
result = geetest.v4.solve(captcha_id="your_captcha_id")
seccode = json.loads(result.response_token)

# 2. Submit to the site's login/verify endpoint
response = client.post(
    "https://example.com/api/login",
    json={
        "username": "user",
        "password": "secretpassword",
        "captcha_id": seccode["captcha_id"],
        "lot_number": seccode["lot_number"],
        "pass_token": seccode["pass_token"],
        "gen_time": seccode["gen_time"],
        "captcha_output": seccode["captcha_output"],
    }
)
```

---

## Dynamic RSA Key Recovery

GeeTest signs challenge responses using RSA public keys shipped inside `gcaptcha4.js`. Occasionally, GeeTest rotates its keys or serves different keys across mirror domains.

PyPasser features an **automatic dynamic key recovery mechanism**:

- Scrapes and parses the active modulus from `gcaptcha4.js` dynamically.
- Maintains an internal cache (`keyring`).
- If GeeTest returns error `-50002` or `-50003` (RSA decryption failed), PyPasser automatically fetches the updated key and retries the request seamlessly.

---

## Exceptions

| Exception | Cause |
|---|---|
| `GeeTestError` | Base exception for GeeTest errors (e.g., unsupported `risk_type`). |
| `GeeTestSolveFailed` | Challenge failed verification or attempts were exhausted. |
| `RequestRateLimited` | GeeTest CDN returned HTTP 429 or 5xx across all mirrors. |
| `RequestFailed` | Network or HTTP connection error. |
