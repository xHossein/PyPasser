# PyPasser

<p align="center">
  <img src="assets/banner.png" alt="PyPasser Banner" width="100%">
</p>

<p align="center">
  <strong>Free, open-source CAPTCHA solver & anti-bot bypass library for Python.</strong><br>
  No paid APIs • No third-party subscription keys • Pure HTTP & Browser automation
</p>

---

## What is PyPasser?

**PyPasser** is a modern Python library designed to solve CAPTCHAs and clear anti-bot interstitial challenges. Its primary strength lies in solving headless, **pure HTTP challenges** — such as reCAPTCHA V3, GeeTest V4, and Lemin Cropped — without launching a browser or running a JavaScript engine.

For visual, audio, or browser-bound challenges (reCAPTCHA V2, Cloudflare Turnstile, Cloudflare Interstitials), PyPasser provides high-level browser automation integrations with built-in stealth engine support.

Every solver in PyPasser exposes both **synchronous** (`solve()`) and **asynchronous** (`asolve()`) interfaces and returns a standardized [`SolverResult`](api/structs.md).

---

## Solvers & Capabilities

| Target | Category | Method | Browser Needed? | Free / Local? |
|---|---|---|:---:|:---:|
| **reCAPTCHA V3** | CAPTCHA | Pure HTTP token forge or DOM hook | **No** | Yes |
| **reCAPTCHA V2** | CAPTCHA | Audio challenge + local Vosk ASR | Yes | Yes |
| **GeeTest V4** | CAPTCHA | Pure HTTP (all 8 risk types + voice fallback) | **No** | Yes |
| **Lemin Cropped** | CAPTCHA | Pure HTTP + local Computer Vision | **No** | Yes |
| **Cloudflare Turnstile** | CAPTCHA | Checkbox interaction + token poller | Yes | Yes |
| **ARCaptcha** | CAPTCHA | Pure HTTP (puzzle CV + Persian voice ASR) | **No** | Yes |
| **Cloudflare Interstitial** | Anti-Bot | Headed stealth browser + cookie extraction | Yes | Yes |
| **ArvanCloud Interstitial** | Anti-Bot | Pure HTTP JSFuck challenge decoder | **No** | Yes |

---

## Quick Example (Pure HTTP)

Solve reCAPTCHA V3, GeeTest V4, or Lemin Cropped challenges in a few seconds without opening a browser:

=== "reCAPTCHA V3 (HTTP)"

    ```python
    from pypasser.captcha import recaptcha

    result = recaptcha.v3.solve(
        anchor_url="https://www.google.com/recaptcha/api2/anchor?ar=1&k=...&co=..."
    )

    if result.is_solved:
        print("g-recaptcha-response:", result.response_token)
    ```

=== "GeeTest V4 (HTTP)"

    ```python
    from pypasser.captcha import geetest

    # Auto-detects whether the site serves slide, ai, match, voice, etc.
    result = geetest.v4.solve(
        captcha_id="54088bb07d2df3c46b79f80300b0abbe",
        risk_type="auto",
    )

    if result.is_solved:
        print("GeeTest seccode JSON:", result.response_token)
    ```

=== "Lemin Cropped (HTTP)"

    ```python
    from pypasser.captcha import lemin

    result = lemin.solve(
        captcha_id="CROPPED_3dfdd5c_d1872b526b794d83ba3b365eb15a200b",
        domain="https://2captcha.com",
    )

    if result.is_solved:
        print("Pre-validation token:", result.response_token["pv_token"])
        print("Answer payload:", result.response_token["answer"])
        print("Challenge ID:", result.response_token["challenge_id"])
    ```

---

## Key Highlights

- **Zero Cost**: Eliminates costly third-party CAPTCHA solving services (2Captcha, Anti-Captcha, CapSolver).
- **Headless HTTP First**: Whenever mathematically possible, challenges are solved via direct wire protocols.
- **Stealth Browser Support**: Native support for [Patchright](https://github.com/kaliiiiiiiiii/patchright), [Playwright](https://playwright.dev/python/), and [Camoufox](https://camoufox.com/) to beat browser fingerprinting.
- **Offline Machine Learning**: Uses local computer vision (Canny edge detection, template correlation) and offline speech recognition ([Vosk](https://alphacephei.com/vosk/)).
