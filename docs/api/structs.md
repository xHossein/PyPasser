# SolverResult Structure

Every solver and bypass in PyPasser returns an instance of the frozen dataclass `SolverResult`. This provides a consistent, immutable response structure across both pure HTTP and browser automation solvers.

---

## Dataclass Definition

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class SolverResult:
    is_solved: bool
    response_token: str | dict[str, str] | None = None
    cookies: dict[str, str] | None = None
    user_agent: str | None = None
```

---

## Attribute Details

### `is_solved` (`bool`)
Indicates whether the challenge was successfully solved or bypassed.

- Always check `result.is_solved` before reading `response_token` or `cookies`.
- Solvers raise exceptions on catastrophic failures, but soft verification rejections may return `is_solved=False`.

### `response_token` (`str | dict[str, str] | None`)
Contains the token(s) to submit back to the protected site or form:

| Solver | Format | Example Content |
|---|---|---|
| **reCAPTCHA V2** | `str` | `"03AFcWeA..."` (`g-recaptcha-response`) |
| **reCAPTCHA V3** | `str` | `"03AFcWeA..."` (`g-recaptcha-response`) |
| **Cloudflare Turnstile** | `str` | `"0.4jX9..."` (`cf-turnstile-response`) |
| **ARCaptcha** | `str` | `"91e0a2b5-..."` (`arcaptcha-token`) |
| **GeeTest V4** | `str` (JSON) | `'{"captcha_id":"...","pass_token":"...","gen_time":"...","captcha_output":"..."}'` |
| **Lemin Cropped** | `dict[str, str]` | `{"pv_token": "...", "answer": "...", "challenge_id": "..."}` |
| **Anti-Bot Interstitials** | `None` | (Anti-bots populate `cookies` instead) |

### `cookies` (`dict[str, str] | None`)
A dictionary of session cookies (`name -> value`) issued upon clearing the challenge.

- Populated by anti-bot interstitial bypasses (`cf_clearance` for Cloudflare, `__arcsjs` and `__arcsjsc` for ArvanCloud).
- Replay these cookies in subsequent HTTP client calls (`httpx.Client(cookies=result.cookies)`).

### `user_agent` (`str | None`)
The exact `User-Agent` string of the client or browser context that solved the challenge.

- Cloudflare and ArvanCloud clearance cookies are cryptographically bound to the solver's User-Agent.
- Always pass `headers={"User-Agent": result.user_agent}` when replaying clearance cookies.

---

## Usage Patterns

### Pattern 1: Handling CAPTCHA Tokens

```python
result = recaptcha.v3.solve(...)

if result.is_solved:
    token = result.response_token
    # Submit token with your form data
    client.post("https://example.com/api/login", data={"g-recaptcha-response": token})
```

### Pattern 2: Handling Dict Tokens (Lemin)

```python
result = lemin.solve(...)

if result.is_solved:
    data = result.response_token
    pv_token = data["pv_token"]
    answer = data["answer"]
    challenge_id = data["challenge_id"]
```

### Pattern 3: Handling Anti-Bot Cookie Replay

```python
result = cloudflare.solve(page)

if result.is_solved:
    headers = {"User-Agent": result.user_agent}
    with httpx.Client(cookies=result.cookies, headers=headers) as client:
        response = client.get("https://example.com/data")
```
