# CAPTCHA Solvers Overview

PyPasser supports all major commercial CAPTCHA providers through high-speed pure HTTP pipelines and stealth browser automation.

---

## Solvers Decision Guide

Use this guide to pick the appropriate solver for your target site:

```mermaid
flowchart TD
    A[Identify Target Challenge] --> B{Challenge Type?}
    B -->|reCAPTCHA V3| C[pypasser.captcha.recaptcha.v3]
    B -->|reCAPTCHA V2| D[pypasser.captcha.recaptcha.v2]
    B -->|GeeTest V4| E[pypasser.captcha.geetest.v4]
    B -->|Lemin Cropped| F[pypasser.captcha.lemin]
    B -->|Cloudflare Turnstile| G[pypasser.captcha.turnstile]
    B -->|ARCaptcha| H[pypasser.captcha.arcaptcha]

    C -->|Pure HTTP or DOM| C1[Returns g-recaptcha-response]
    D -->|Browser + Vosk ASR| D1[Returns g-recaptcha-response]
    E -->|Pure HTTP Wire Protocol| E1[Returns seccode JSON]
    F -->|Pure HTTP + CV Match| F1[Returns pv_token & answer dict]
    G -->|Browser Automation| G1[Returns cf-turnstile-response]
    H -->|Pure HTTP or DOM| H1[Returns arcaptcha-token]
```

---

## Solvers Matrix

| Solver | Import Path | Primary Input | Runtime | Output Format |
|---|---|---|:---:|---|
| [**reCAPTCHA V3**](recaptcha-v3.md) | `pypasser.captcha.recaptcha.v3` | `anchor_url` or `page` | HTTP / Browser | String token |
| [**reCAPTCHA V2**](recaptcha-v2.md) | `pypasser.captcha.recaptcha.v2` | `page` | Browser | String token |
| [**GeeTest V4**](geetest-v4.md) | `pypasser.captcha.geetest.v4` | `captcha_id` | HTTP | JSON seccode string |
| [**Lemin Cropped**](lemin-cropped.md) | `pypasser.captcha.lemin` | `captcha_id`, `domain` | HTTP | Dict (`pv_token`, `answer`, `challenge_id`) |
| [**Cloudflare Turnstile**](turnstile.md) | `pypasser.captcha.turnstile` | `page` | Browser | String token |
| [**ARCaptcha**](arcaptcha.md) | `pypasser.captcha.arcaptcha` | `site_key`, `domain` or `page` | HTTP / Browser | String challenge token |

---

## Common Features

### Dual Sync & Async APIs
Every solver module exports both synchronous and asynchronous top-level functions:

- `solve(...)`
- `asolve(...)`

### Standard Return Type
All solvers return a frozen [`SolverResult`](../api/structs.md) object:
```python
result = solver.solve(...)
if result.is_solved:
    token = result.response_token
```

### Proxy Support
HTTP-based solvers accept a standard proxy string across HTTP, HTTPS, SOCKS4, and SOCKS5 schemes:
```python
result = lemin.solve(..., proxy="socks5://user:pass@127.0.0.1:1080")
```
