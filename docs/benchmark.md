# Live Benchmark

PyPasser includes an automated live benchmark suite that tests every solver and anti-bot bypass against **real live production endpoints**, verifies the generated tokens with each demo's server verification API, and replays anti-bot clearance cookies over plain HTTP.

Two runner scripts are provided:

- **`benchmark/run.py`**: Synchronous test harness.
- **`benchmark/run_async.py`**: Asynchronous test harness.

---

## Live Benchmark Results

```text
+-----------------------------------------+------------+---------------------------+--------+--------+------------------------------------------+
| target                                  | browser    | strategy                  | result | bypass | detail                                   |
+-----------------------------------------+------------+---------------------------+--------+--------+------------------------------------------+
| reCAPTCHA V2                            | patchright | v2                        | PASS   |   4.3s | verify={"success": true, "challenge_ts": |
| reCAPTCHA V2 invisible                  | patchright | v2                        | PASS   |   7.6s | verify={"success": true, "challenge_ts": |
| reCAPTCHA V2 callback                   | patchright | v2                        | PASS   |   5.2s | verify={"success": true, "challenge_ts": |
| reCAPTCHA V2 Enterprise                 | patchright | v2                        | PASS   |   4.1s | verify={"success": true, "challenge_ts": |
| reCAPTCHA V3                            | (HTTP Req) | v3                        | PASS   |   1.2s | score=0.9                                |
| reCAPTCHA V3 Enterprise                 | (HTTP Req) | v3                        | PASS   |   1.1s | score=0.9                                |
| Cloudflare Turnstile                    | patchright | turnstile                 | PASS   |   5.6s | verify={"challenge_ts": "2026-10-14T13:2 |
| Cloudflare interstitial (steamdb.info)  | patchright | CF interstitial (antibot) | PASS   |   8.9s | replay 200 SteamDB | Database of everyth |
| ArvanCloud interstitial (esale.ikco.ir) | (HTTP Req) | AC interstitial (antibot) | PASS   |   1.4s | replay 200 فروش اینترنتی محصولات ایرانخ |
| ARCaptcha puzzle hidden                 | (HTTP Req) | arcaptcha                 | PASS   |   0.7s | accepted                                 |
| ARCaptcha puzzle                        | (HTTP Req) | arcaptcha                 | PASS   |   0.6s | accepted                                 |
| ARCaptcha 9-grid image (voice)          | (HTTP Req) | arcaptcha                 | PASS   |   7.6s | accepted                                 |
| GeeTest V4 auto-detect                  | (HTTP Req) | geetest                   | PASS   |   5.1s | token=5e5f9abe                           |
| GeeTest V4 slide                        | (HTTP Req) | geetest                   | PASS   |   2.4s | token=09db69c3                           |
| GeeTest V4 ai                           | (HTTP Req) | geetest                   | PASS   |   1.5s | token=e2fe0b29                           |
| GeeTest V4 winlinze                     | (HTTP Req) | geetest                   | PASS   |   1.1s | token=a28e316d                           |
| GeeTest V4 match                        | (HTTP Req) | geetest                   | PASS   |   1.3s | token=7cd42d43                           |
| GeeTest V4 nine (voice)                 | (HTTP Req) | geetest                   | PASS   |   2.8s | token=be043368                           |
| GeeTest V4 icon (voice)                 | (HTTP Req) | geetest                   | PASS   |   2.7s | token=cba3b40f                           |
| GeeTest V4 svg_icon                     | (HTTP Req) | geetest                   | PASS   |   1.7s | token=19b497b8                           |
| GeeTest V4 voice                        | (HTTP Req) | geetest                   | PASS   |   2.3s | token=87ad862b                           |
| GeeTest V4 invisible-bind (ai)          | (HTTP Req) | geetest                   | PASS   |   1.4s | token=60054b0d                           |
| Lemin cropped (2captcha demo)           | (HTTP Req) | lemin                     | PASS   |   3.7s | pv_token=gAAAAABq2cgU                    |
+-----------------------------------------+------------+---------------------------+--------+--------+------------------------------------------+
```

> **Note on timing**: The `bypass` column records pure solver execution time only, excluding page navigation, DOM discovery, and post-solve HTTP verification calls.

---

## Running the Benchmark

### 1. Prerequisites

Install all extras and browser binaries:

```bash
pip install "PyPasser[all]"
patchright install chromium
```

---

### 2. Basic Execution

=== "Sync Runner"

    ```bash
    # Run all 23 targets
    python benchmark/run.py
    ```

=== "Async Runner"

    ```bash
    # Run all 23 targets asynchronously
    python benchmark/run_async.py
    ```

---

### 3. Target Filtering

Filter targets by group or individual target slugs:

```bash
# Filter by group name:
python benchmark/run.py --targets recaptcha
python benchmark/run.py --targets geetest
python benchmark/run.py --targets lemin
python benchmark/run.py --targets cloudflare
python benchmark/run.py --targets arcaptcha
python benchmark/run.py --targets antibots

# Filter by comma-separated slugs:
python benchmark/run.py --targets v2-callback,turnstile,lemin
```

---

### 4. Browser Selection & Headless Options

```bash
# Select browser automation engine:
python benchmark/run.py --browser patchright   # Default (Stealth)
python benchmark/run.py --browser playwright   # Standard
python benchmark/run.py --browser camoufox     # Firefox anti-detect

# Display options:
python benchmark/run.py --headed     # Shows the browser UI
python benchmark/run.py --headless   # Forces headless (Note: Cloudflare interstitial will fail)
```

The Cloudflare interstitial test automatically opens a headed window because Cloudflare blocks headless browsers on high-security challenge pages.
