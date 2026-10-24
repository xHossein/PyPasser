<p align="center">
  <h1 align="center">PyPasser</h1>
  <p align="center">
    Free, open-source CAPTCHA solver for Python (no paid APIs) — solve reCAPTCHA (V2, V3), GeeTest V4, Lemin, Cloudflare Turnstile, ARCaptcha, and anti-bot walls via pure HTTP requests and browser automation.
  </p>
  <p align="center">
    <a href="https://pypi.org/project/PyPasser/"><img src="https://img.shields.io/pypi/v/PyPasser?color=blue" alt="PyPI"></a>
    <img alt="Python Version from PEP 621 TOML" src="https://img.shields.io/python/required-version-toml?tomlFilePath=https%3A%2F%2Fraw.githubusercontent.com%2FxHossein%2FPyPasser%2Frefs%2Fheads%2Fmaster%2Fpyproject.toml">
    <img alt="PyPI Downloads" src="https://img.shields.io/pypi/dm/pypasser">
    <a href="https://github.com/xHossein/PyPasser/blob/master/LICENSE"><img src="https://img.shields.io/github/license/xHossein/PyPasser" alt="License"></a>
    <a href="https://xhossein.github.io/PyPasser/"><img src="https://img.shields.io/badge/docs-GitHub_Pages-blue.svg" alt="Documentation"></a>
  </p>
</p>

---

<p align="center"><img src="docs/assets/banner.png" alt="PyPasser"></p>

**PyPasser** is a free, open-source Python library for bypassing and solving CAPTCHAs and clearing anti-bot interstitial challenges.

Its main feature is solving **pure HTTP challenges** — such as reCAPTCHA V3, GeeTest V4, and Lemin Cropped — without launching a browser or running a JavaScript engine. For challenges that require a browser (reCAPTCHA V2, Cloudflare Turnstile, anti-bot walls), it drives stealth automation engines like [Patchright](https://github.com/Kaliiiiiiiiii-Vinyzu/patchright) or Playwright and extracts tokens and clearance cookies for subsequent HTTP replay.

> 📖 **Full Documentation & API Guides**: **[https://xhossein.github.io/PyPasser/](https://xhossein.github.io/PyPasser/)**

---

## Supported Solvers

| Target | Method | Browser Needed? | Documentation |
|---|---|:---:|---|
| **reCAPTCHA V3** | Pure HTTP anchor token forge | **No** | [reCAPTCHA V3 Guide](https://xhossein.github.io/PyPasser/solvers/recaptcha-v3/) |
| **reCAPTCHA V2** | Checkbox + offline Vosk audio transcription | Yes | [reCAPTCHA V2 Guide](https://xhossein.github.io/PyPasser/solvers/recaptcha-v2/) |
| **GeeTest V4** | Pure HTTP wire protocol (all 8 risk types + voice fallback) | **No** | [GeeTest V4 Guide](https://xhossein.github.io/PyPasser/solvers/geetest-v4/) |
| **Lemin Cropped** | Pure HTTP + local Computer Vision contour match | **No** | [Lemin Cropped Guide](https://xhossein.github.io/PyPasser/solvers/lemin-cropped/) |
| **Cloudflare Turnstile** | Embedded & managed challenge automation | Yes | [Turnstile Guide](https://xhossein.github.io/PyPasser/solvers/turnstile/) |
| **ARCaptcha** | Pure HTTP puzzle CV + Persian Vosk voice fallback | **No** | [ARCaptcha Guide](https://xhossein.github.io/PyPasser/solvers/arcaptcha/) |
| **Cloudflare Interstitial** | "Just a moment..." wall clearance → `cf_clearance` cookie | Yes | [Cloudflare Interstitial Guide](https://xhossein.github.io/PyPasser/antibots/cloudflare/) |
| **ArvanCloud Interstitial** | Pure HTTP JSFuck decoder → `__arcsjs` cookies | **No** | [ArvanCloud Interstitial Guide](https://xhossein.github.io/PyPasser/antibots/arvancloud/) |

---

## Installation

```bash
pip install PyPasser
```

Install capability extras depending on the solvers you use:

```bash
pip install "PyPasser[stealth,speech]"        # Browser solves + audio (V2, Turnstile)
pip install "PyPasser[stealth,speech,vision]" # + ARCaptcha, GeeTest, Lemin
pip install "PyPasser[all]"                   # Everything bundled
```

If using browser automation, install the recommended stealth browser engine:

```bash
patchright install chromium
```

👉 See [Installation Guide](https://xhossein.github.io/PyPasser/getting-started/installation/) for speech models and browser setup.

---

## Quick Examples

### 1. Pure HTTP Solving (No Browser)

```python
from pypasser.captcha import lemin, geetest, recaptcha

# Lemin Cropped jigsaw puzzle
result = lemin.solve(
    captcha_id="CROPPED_3dfdd5c_d1872b526b794d83ba3b365eb15a200b",
    domain="https://2captcha.com",
)
if result.is_solved:
    print("Lemin pv_token:", result.response_token["pv_token"])

# GeeTest V4 (Auto-detects risk type: slide, ai, match, voice, etc.)
gt_result = geetest.v4.solve("54088bb07d2df3c46b79f80300b0abbe", risk_type="auto")
if gt_result.is_solved:
    print("GeeTest seccode:", gt_result.response_token)

# reCAPTCHA V3
v3_result = recaptcha.v3.solve("https://www.google.com/recaptcha/api2/anchor?ar=1&k=...")
if v3_result.is_solved:
    print("V3 token:", v3_result.response_token)
```

### 2. Browser Automation (Turnstile & V2)

```python
from patchright.sync_api import sync_playwright
from pypasser.captcha import turnstile

with sync_playwright() as pw:
    page = pw.chromium.launch(headless=False).new_page()
    page.goto("https://example.com/with-turnstile")
    result = turnstile.solve(page)
    print("Turnstile token:", result.response_token)
```

### 3. Anti-Bot Clearance & HTTP Cookie Replay

```python
import httpx
from patchright.sync_api import sync_playwright
from pypasser.antibot import cloudflare

url = "https://protected-site.com"

# 1. Clear wall in browser
with sync_playwright() as pw:
    page = pw.chromium.launch(headless=False).new_page()
    page.goto(url)
    result = cloudflare.solve(page, timeout=60)

# 2. Replay cookies over plain HTTP (no browser)
headers = {"User-Agent": result.user_agent}
with httpx.Client(cookies=result.cookies, headers=headers) as client:
    response = client.get(url)
    print("Status:", response.status_code)
```

👉 See [Quickstart Guide](https://xhossein.github.io/PyPasser/getting-started/quickstart/) for async examples and Playwright injection.

---

## Live Benchmark

All solvers are continuously verified against live production endpoints:

```text
+-----------------------------------------+------------+---------------------------+--------+-----------+
| target                                  | browser    | strategy                  | result | bypass    |
+-----------------------------------------+------------+---------------------------+--------+-----------+
| reCAPTCHA V2 (all variants)             | patchright | v2                        | PASS   | 4.1s–7.6s |
| reCAPTCHA V3 & Enterprise               | (HTTP Req) | v3                        | PASS   |      1.2s |
| Cloudflare Turnstile                    | patchright | turnstile                 | PASS   |      5.6s |
| Cloudflare interstitial (steamdb.info)  | patchright | CF interstitial (antibot) | PASS   |      8.9s |
| ArvanCloud interstitial (esale.ikco.ir) | (HTTP Req) | AC interstitial (antibot) | PASS   |      1.4s |
| ARCaptcha (puzzle, hidden, voice)       | (HTTP Req) | arcaptcha                 | PASS   | 0.6s–7.6s |
| GeeTest V4 (all 8 risk types + auto)    | (HTTP Req) | geetest                   | PASS   | 1.1s–5.1s |
| Lemin cropped (2captcha demo)           | (HTTP Req) | lemin                     | PASS   |      3.7s |
+-----------------------------------------+------------+---------------------------+--------+-----------+
```

Run benchmarks locally:

```bash
python benchmark/run.py
python benchmark/run_async.py
```

👉 See full benchmark details and CLI flags in the [Benchmark Documentation](https://xhossein.github.io/PyPasser/benchmark/).

---

## Documentation Links

- 📚 **[Documentation Home](https://xhossein.github.io/PyPasser/)**
- 🚀 **[Getting Started & Installation](https://xhossein.github.io/PyPasser/getting-started/installation/)**
- 🛡️ **[CAPTCHA Solvers Guide](https://xhossein.github.io/PyPasser/solvers/)**
- 🧱 **[Anti-Bot Interstitials & Replay](https://xhossein.github.io/PyPasser/antibots/)**
- 📊 **[Live Benchmarks](https://xhossein.github.io/PyPasser/benchmark/)**
- ⚙️ **[API Reference (`SolverResult` & Exceptions)](https://xhossein.github.io/PyPasser/api/structs/)**

---

## License

[MIT](LICENSE) © [xHossein](https://github.com/xHossein)

---

## Disclaimer

**This project is intended strictly for educational, research, and authorized testing purposes. The authors and contributors assume no liability for misuse, damages, or violations of third-party Terms of Service. Users are solely responsible for ensuring compliance with all applicable laws and website policies.**
