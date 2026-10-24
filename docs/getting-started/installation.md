# Installation

PyPasser is organized into a modular design. The core package is lightweight with minimal dependencies (`httpx[socks]` and `cryptography`), allowing you to install only what your application requires.

## Core Installation

Install the base package from PyPI:

```bash
pip install PyPasser
```

The base package supports:

- **reCAPTCHA V3** (Pure HTTP anchor URL mode)
- **ArvanCloud Interstitial** (Pure HTTP JSFuck challenge clearance)

---

## Capability Extras

PyPasser defines optional dependency groups for specialized capabilities:

```bash
# Browser automation (Playwright)
pip install "PyPasser[browsers]"

# Stealth browser engines (Patchright + Camoufox) — Recommended for Turnstile & V2
pip install "PyPasser[stealth]"

# Speech-to-text recognition (Vosk + ffmpeg + pydub)
pip install "PyPasser[speech]"

# Computer vision & template matching (Pillow + NumPy)
pip install "PyPasser[vision]"

# All capabilities bundled
pip install "PyPasser[all]"
```

---

## Extras Requirement Matrix

Consult this table to determine which extras your target solver requires:

| Target Module | Required Extra | What It Installs |
|---|---|---|
| `pypasser.captcha.recaptcha.v3` (HTTP) | *None (Core)* | `httpx[socks]`, `cryptography` |
| `pypasser.captcha.recaptcha.v3` (Page mode) | `[browsers]` or `[stealth]` | `playwright` or `patchright` |
| `pypasser.captcha.recaptcha.v2` | `[browsers]` + `[speech]` | `playwright`, `vosk`, `imageio-ffmpeg`, `pydub` |
| `pypasser.captcha.geetest.v4` | `[vision]` + `[speech]` | `pillow`, `numpy`, `vosk`, `imageio-ffmpeg` |
| `pypasser.captcha.lemin` | `[vision]` | `pillow`, `numpy` |
| `pypasser.captcha.turnstile` | `[stealth]` (recommended) or `[browsers]` | `patchright` or `playwright` |
| `pypasser.captcha.arcaptcha` | `[vision]` + `[speech]` | `pillow`, `numpy`, `vosk`, `imageio-ffmpeg` |
| `pypasser.antibot.cloudflare` | `[stealth]` (recommended) or `[browsers]` | `patchright` or `playwright` |
| `pypasser.antibot.arvancloud` | *None (Core)* | `httpx[socks]` |

---

## Browser Driver Setup

If you use any browser-based solver (`recaptcha.v2`, `turnstile`, `antibot.cloudflare`), ensure your browser binaries are installed:

=== "Patchright (Stealth, Recommended)"

    ```bash
    pip install "PyPasser[stealth]"
    patchright install chromium
    ```

=== "Standard Playwright"

    ```bash
    pip install "PyPasser[browsers]"
    playwright install chromium
    ```

=== "Camoufox (Firefox Anti-detect)"

    ```bash
    pip install "PyPasser[stealth]"
    python -m camoufox fetch
    ```

---

## Offline Speech Models (Vosk)

Solvers utilizing audio recognition (`recaptcha.v2`, `arcaptcha`, `geetest.v4` voice) download their required Vosk language models automatically on the first run into `~/.cache/vosk/` or the local system cache.

- **English model**: `vosk-model-small-en-us-0.15` (~40 MB)
- **Persian model**: `vosk-model-fa-0.5` (~1.4 GB, only for ARCaptcha voice)

Subsequent runs run completely offline from the local cache.
