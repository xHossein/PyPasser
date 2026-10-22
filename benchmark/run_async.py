"""Live benchmark for every PyPasser solver (asynchronous).

Usage::

    python benchmark/run_async.py
    python benchmark/run_async.py --targets recaptcha
    python benchmark/run_async.py --browser playwright
    python benchmark/run_async.py --browser camoufox --headed
    python benchmark/run_async.py --targets cloudflare --headless
"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
import sys
import time
from contextlib import asynccontextmanager, nullcontext
from dataclasses import dataclass
from typing import Any, Awaitable, Callable

import httpx

from pypasser.antibot import arvancloud, cloudflare
from pypasser.antibot.arvancloud.challenge import is_challenge
from pypasser.captcha import arcaptcha, geetest, lemin, recaptcha, turnstile

BASE = "https://2captcha.com/demo"
VERIFY_URL = "https://2captcha.com/api/v1/captcha-demo/recaptcha/verify"
ENTERPRISE_VERIFY_URL = "https://2captcha.com/api/v1/captcha-demo/recaptcha-enterprise/verify"
TURNSTILE_VERIFY_URL = "https://2captcha.com/api/v1/captcha-demo/cloudflare-turnstile/verify"

# GeeTest demo id; it serves every supported risk_type on request.
GEETEST_ID = "54088bb07d2df3c46b79f80300b0abbe"
# Lemin demo captcha id and verify URL on 2captcha.com.
LEMIN_ID = "CROPPED_3dfdd5c_d1872b526b794d83ba3b365eb15a200b"
LEMIN_VERIFY_URL = "https://2captcha.com/api/v1/captcha-demo/lemin/verify"
VERIFY_HEADERS = {
    "accept": "*/*",
    "content-type": "application/json",
    "origin": "https://2captcha.com",
    "referer": "https://2captcha.com/demo",
}

BROWSERS = ("patchright", "playwright", "camoufox")
_TITLE_RE = re.compile(r"<title>(.*?)</title>", re.S | re.I)


@dataclass
class Target:
    slug: str
    label: str
    strategy: str
    group: str
    runner_key: str = ""
    url: str = ""
    site_key: str = ""
    domain: str = ""
    verify_url: str = ""
    token_field: str = "answer"
    opens_popup: bool = False
    risk_type: str = ""

    def __post_init__(self) -> None:
        if not self.runner_key:
            self.runner_key = self.strategy


TARGETS: list[Target] = [
    Target("v2", "reCAPTCHA V2", "v2", "recaptcha",
           url=f"{BASE}/recaptcha-v2", verify_url=VERIFY_URL),
    Target("v2-invisible", "reCAPTCHA V2 invisible", "v2", "recaptcha",
           url=f"{BASE}/recaptcha-v2-invisible", verify_url=VERIFY_URL, opens_popup=True),
    Target("v2-callback", "reCAPTCHA V2 callback", "v2", "recaptcha",
           url=f"{BASE}/recaptcha-v2-callback", verify_url=VERIFY_URL),
    Target("v2-enterprise", "reCAPTCHA V2 Enterprise", "v2", "recaptcha",
           url=f"{BASE}/recaptcha-v2-enterprise", verify_url=VERIFY_URL),

    Target("v3", "reCAPTCHA V3", "v3", "recaptcha",
           url=f"{BASE}/recaptcha-v3", verify_url=VERIFY_URL),
    Target("v3-enterprise", "reCAPTCHA V3 Enterprise", "v3", "recaptcha",
           url=f"{BASE}/recaptcha-v3-enterprise", verify_url=ENTERPRISE_VERIFY_URL,
           token_field="token"),

    Target("turnstile", "Cloudflare Turnstile", "turnstile", "cloudflare",
           url=f"{BASE}/cloudflare-turnstile", verify_url=TURNSTILE_VERIFY_URL,
           token_field="response"),
    Target("cloudflare-interstitial", "Cloudflare interstitial (steamdb.info)",
           "CF interstitial (antibot)", "cloudflare",
           runner_key="interstitial", url="https://steamdb.info/"),

    Target("arvancloud-ikco", "ArvanCloud interstitial (esale.ikco.ir)",
           "AC interstitial (antibot)", "arvancloud",
           runner_key="arvancloud", url="https://esale.ikco.ir/"),

    Target("arcaptcha-hidden", "ARCaptcha puzzle hidden", "arcaptcha", "arcaptcha",
           site_key="jqz10q84eu", domain="arcaptcha.co"),
    Target("arcaptcha-demo", "ARCaptcha puzzle", "arcaptcha", "arcaptcha",
           site_key="d6ggpvy684", domain="demo.arcaptcha.co"),
    Target("arcaptcha-classic", "ARCaptcha 9-grid image (voice)", "arcaptcha", "arcaptcha",
           site_key="vm6spkx59m", domain="arcaptcha.co"),

    Target("geetest-auto", "GeeTest V4 auto-detect", "geetest", "geetest",
           site_key=GEETEST_ID),
    Target("geetest-slide", "GeeTest V4 slide", "geetest", "geetest",
           site_key=GEETEST_ID, risk_type="slide"),
    Target("geetest-ai", "GeeTest V4 ai", "geetest", "geetest",
           site_key=GEETEST_ID, risk_type="ai"),
    Target("geetest-winlinze", "GeeTest V4 winlinze", "geetest", "geetest",
           site_key=GEETEST_ID, risk_type="winlinze"),
    Target("geetest-match", "GeeTest V4 match", "geetest", "geetest",
           site_key=GEETEST_ID, risk_type="match"),
    Target("geetest-nine", "GeeTest V4 nine (voice)", "geetest", "geetest",
           site_key=GEETEST_ID, risk_type="nine"),
    Target("geetest-icon", "GeeTest V4 icon (voice)", "geetest", "geetest",
           site_key=GEETEST_ID, risk_type="icon"),
    Target("geetest-svg-icon", "GeeTest V4 svg_icon", "geetest", "geetest",
           site_key=GEETEST_ID, risk_type="svg_icon"),
    Target("geetest-voice", "GeeTest V4 voice", "geetest", "geetest",
           site_key=GEETEST_ID, risk_type="voice"),
    Target("geetest-invisible-bind", "GeeTest V4 invisible-bind (ai)",
           "geetest", "geetest", site_key="99b142aaece96330d0f3ffb565ffb3ef"),

    Target("lemin", "Lemin cropped (2captcha demo)", "lemin", "lemin",
           site_key=LEMIN_ID, domain="https://2captcha.com",
           verify_url=LEMIN_VERIFY_URL),
]

GROUPS = {
    "recaptcha": [t.slug for t in TARGETS if t.group == "recaptcha"],
    "cloudflare": [t.slug for t in TARGETS if t.group == "cloudflare"],
    "arvancloud": [t.slug for t in TARGETS if t.group == "arvancloud"],
    "arcaptcha": [t.slug for t in TARGETS if t.group == "arcaptcha"],
    "geetest": [t.slug for t in TARGETS if t.group == "geetest"],
    "lemin": [t.slug for t in TARGETS if t.group == "lemin"],
    "antibots": [t.slug for t in TARGETS
                 if t.runner_key == "interstitial" or t.group == "arvancloud"],
}

BROWSER_RUNNERS = {"v2", "v3", "turnstile", "interstitial"}


@dataclass
class Row:
    target: str
    strategy: str
    browser: str
    result: str
    bypass_s: float
    detail: str


def _page_title(html: str) -> str:
    m = _TITLE_RE.search(html)
    return re.sub(r"\s+", " ", m.group(1)).strip()[:60] if m else ""


async def _read_anchor(page: Any) -> str:
    deadline = time.monotonic() + 15.0
    while time.monotonic() < deadline:
        for sel in (
            "iframe[title='reCAPTCHA']",
            "iframe[title^='recaptcha challenge']",
            "iframe[name^='a-']",
        ):
            try:
                loc = page.locator(sel).first
                if await loc.count() > 0:
                    src = await loc.get_attribute("src")
                    if src and "anchor?" in src:
                        return src
            except Exception:
                continue
        await page.wait_for_timeout(100)
    return ""


def _site_key(anchor: str) -> str:
    if "?" not in anchor:
        return ""
    for part in anchor.split("?", 1)[1].split("&"):
        if part.startswith("k="):
            return part[2:]
    return ""


async def _verify(token: str, site_key: str, target: Target) -> dict:
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(
                target.verify_url,
                headers=VERIFY_HEADERS,
                json={target.token_field: token, "siteKey": site_key},
            )
            return r.json()
    except Exception as exc:
        return {"error": str(exc)}


async def _replay(url: str, result: Any) -> httpx.Response:
    headers = {"User-Agent": result.user_agent} if result.user_agent else {}
    async with httpx.AsyncClient(
        cookies=result.cookies or {},
        headers=headers,
        timeout=30,
        follow_redirects=True,
    ) as client:
        return await client.get(url)


async def run_v2(page: Any, target: Target) -> tuple[bool, str, float]:
    if target.opens_popup:
        try:
            await page.get_by_role("button", name="Check").first.click(timeout=5000)
        except Exception:
            pass

    t0 = time.monotonic()
    result = await recaptcha.v2.asolve(page)
    bypass_s = time.monotonic() - t0

    if not result.is_solved:
        return False, "not solved", bypass_s
    token = await page.evaluate(
        "() => document.querySelector('.g-recaptcha-response')?.value || ''"
    )
    if not token:
        return False, "solved but no token in DOM", bypass_s
    anchor = await _read_anchor(page)
    payload = await _verify(token, _site_key(anchor), target)
    score = payload.get("score")
    detail = f"score={score}" if score is not None else f"verify={json.dumps(payload)[:60]}"
    return bool(payload.get("success")), detail, bypass_s


async def run_v3(page: Any, target: Target) -> tuple[bool, str, float]:
    anchor = await _read_anchor(page)
    if not anchor:
        return False, "no anchor URL", 0.0
    site_key = _site_key(anchor)

    t0 = time.monotonic()
    result = await recaptcha.v3.asolve(anchor)
    bypass_s = time.monotonic() - t0

    if not result.is_solved or not result.response_token:
        return False, "no token", bypass_s
    payload = await _verify(result.response_token, site_key, target)
    score = payload.get("score") or payload.get("riskAnalysis", {}).get("score")
    detail = f"score={score}" if score is not None else f"verify={json.dumps(payload)[:60]}"
    return bool(payload.get("success")), detail, bypass_s


async def run_turnstile(page: Any, target: Target) -> tuple[bool, str, float]:
    t0 = time.monotonic()
    result = await turnstile.asolve(page, timeout=30)
    bypass_s = time.monotonic() - t0

    if not result.is_solved or not result.response_token:
        return False, "no token", bypass_s
    payload = await _verify(result.response_token, "", target)
    return bool(payload.get("success")), f"verify={json.dumps(payload)[:60]}", bypass_s


async def run_interstitial(page: Any, target: Target) -> tuple[bool, str, float]:
    t0 = time.monotonic()
    result = await cloudflare.asolve(page, timeout=60)
    bypass_s = time.monotonic() - t0

    if not result.is_solved:
        return False, "not cleared (headless or IP blocked)", bypass_s
    resp = await _replay(target.url, result)
    blocked = resp.status_code in (403, 503) or "just a moment" in resp.text.lower()
    title = _page_title(resp.text)
    ok = not blocked and resp.status_code < 400
    return ok, f"replay {resp.status_code} {'BLOCKED' if blocked else title}", bypass_s


async def run_arvancloud(_page: Any, target: Target) -> tuple[bool, str, float]:
    t0 = time.monotonic()
    result = await arvancloud.asolve(target.url, timeout=30, attempts=3)
    bypass_s = time.monotonic() - t0

    if not result.is_solved:
        return False, "not solved", bypass_s
    resp = await _replay(target.url, result)
    challenged = is_challenge(resp.text)
    title = _page_title(resp.text)
    ok = not challenged and resp.status_code < 400
    return ok, f"replay {resp.status_code} {'CHALLENGED' if challenged else title}", bypass_s


async def run_arcaptcha(_page: Any, target: Target) -> tuple[bool, str, float]:
    t0 = time.monotonic()
    result = await arcaptcha.asolve(target.site_key, domain=target.domain, attempts=3)
    bypass_s = time.monotonic() - t0

    if not result.is_solved:
        return False, "no token", bypass_s
    return True, "accepted", bypass_s


async def run_geetest(_page: Any, target: Target) -> tuple[bool, str, float]:
    t0 = time.monotonic()
    result = await geetest.v4.asolve(
        target.site_key, risk_type=target.risk_type or "auto", attempts=1
    )
    bypass_s = time.monotonic() - t0

    if not result.is_solved:
        return False, "no token", bypass_s
    seccode = json.loads(result.response_token)
    ok = bool(seccode.get("pass_token") and seccode.get("captcha_output"))
    detail = f"token={str(seccode.get('pass_token'))[:8]}"
    return ok, detail, bypass_s


async def run_lemin(_page: Any, target: Target) -> tuple[bool, str, float]:
    t0 = time.monotonic()
    result = await lemin.asolve(
        target.site_key, domain=target.domain, attempts=3,
    )
    bypass_s = time.monotonic() - t0

    if not result.is_solved:
        return False, "not solved", bypass_s
    data = result.response_token
    payload = {"answer": data["answer"], "challenge_id": data["challenge_id"]}
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(target.verify_url, headers=VERIFY_HEADERS, json=payload)
    body = r.json()
    ok = bool(body.get("success"))
    detail = f"pv_token={data['pv_token'][:12]}"
    return ok, detail, bypass_s


RUNNERS: dict[str, Callable[..., Awaitable[tuple[bool, str, float]]]] = {
    "v2": run_v2,
    "v3": run_v3,
    "turnstile": run_turnstile,
    "interstitial": run_interstitial,
    "arvancloud": run_arvancloud,
    "arcaptcha": run_arcaptcha,
    "geetest": run_geetest,
    "lemin": run_lemin,
}


@asynccontextmanager
async def _open_browser(engine: str, headed: bool):
    if engine == "camoufox":
        from camoufox.async_api import AsyncCamoufox

        async with AsyncCamoufox(headless=not headed) as browser:
            yield browser
        return

    if engine == "patchright":
        from patchright.async_api import async_playwright
    else:
        from playwright.async_api import async_playwright

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=not headed)
        try:
            ua = None
            if not headed:
                probe = await browser.new_page()
                raw_ua = await probe.evaluate("navigator.userAgent")
                ua = raw_ua.replace("HeadlessChrome", "Chrome")
                await probe.close()
            yield _BrowserWrapper(browser, ua)
        finally:
            await browser.close()


class _BrowserWrapper:
    def __init__(self, browser: Any, user_agent: str | None) -> None:
        self._browser = browser
        self._ua = user_agent

    async def new_page(self) -> Any:
        if self._ua:
            return await self._browser.new_page(user_agent=self._ua)
        return await self._browser.new_page()


def select_targets(spec: str) -> list[Target]:
    if spec.strip().lower() == "all":
        return list(TARGETS)
    wanted = [n.strip().lower() for n in spec.split(",") if n.strip()]
    expanded = [slug for n in wanted for slug in GROUPS.get(n, [n])]
    known = {t.slug: t for t in TARGETS}
    if not expanded:
        raise SystemExit("--targets needs at least one name (or 'all')")
    unknown = [s for s in expanded if s not in known]
    if unknown:
        valid = ", ".join([*GROUPS, *known, "all"])
        raise SystemExit(f"unknown: {', '.join(unknown)}. Valid: {valid}")
    seen: set[str] = set()
    return [t for t in TARGETS if t.slug in expanded and not (t.slug in seen or seen.add(t.slug))]


async def run_target(target: Target, browser: Any, engine: str) -> Row:
    runner = RUNNERS[target.runner_key]
    browser_label = engine if target.runner_key in BROWSER_RUNNERS else "—"

    if target.runner_key not in BROWSER_RUNNERS:
        try:
            ok, detail, bypass_s = await runner(None, target)
        except Exception as exc:
            ok, detail, bypass_s = False, f"{type(exc).__name__}: {exc}", 0.0
        return Row(target.label, target.strategy, browser_label,
                   "PASS" if ok else "FAIL", bypass_s, detail)

    page = await browser.new_page()
    try:
        await page.set_viewport_size({"width": 1280, "height": 800})
        await page.goto(target.url, wait_until="domcontentloaded")
        await page.wait_for_timeout(500)
        ok, detail, bypass_s = await runner(page, target)
    except Exception as exc:
        ok, detail, bypass_s = False, f"{type(exc).__name__}: {exc}", 0.0
    finally:
        await page.close()

    return Row(target.label, target.strategy, browser_label,
               "PASS" if ok else "FAIL", bypass_s, detail)


def _print_table(rows: list[Row]) -> None:
    hdr = ("target", "browser", "strategy", "result", "bypass", "detail")
    widths = [
        max(len(hdr[0]), max((len(r.target) for r in rows), default=0)),
        max(len(hdr[1]), max((len(r.browser) for r in rows), default=0)),
        max(len(hdr[2]), max((len(r.strategy) for r in rows), default=0)),
        len(hdr[3]),
        len(hdr[4]),
        len(hdr[5]),
    ]
    w = widths
    bar = ["-" * c for c in (*w[:5], 40)]
    sep = "+-" + "-+-".join(bar) + "-+"

    print(sep)
    print(f"| {hdr[0]:<{w[0]}} | {hdr[1]:<{w[1]}} | {hdr[2]:<{w[2]}} "
          f"| {hdr[3]:<{w[3]}} | {hdr[4]:<{w[4]}} | {'detail':<40} |")
    print(sep)
    for r in rows:
        bypass = f"{r.bypass_s:.1f}s"
        print(f"| {r.target:<{w[0]}} | {r.browser:<{w[1]}} | {r.strategy:<{w[2]}} "
              f"| {r.result:<{w[3]}} | {bypass:>{w[4]}} | {r.detail[:40]:<40} |")
    print(sep)

    passed = sum(1 for r in rows if r.result == "PASS")
    print(f"\n{passed}/{len(rows)} passed")


def _force_utf8() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass


async def amain() -> None:
    _force_utf8()

    parser = argparse.ArgumentParser(description="PyPasser live benchmark (async)")
    parser.add_argument("--targets", default="all",
                        help=f"comma-separated slugs/groups ({', '.join([*GROUPS, 'all'])})")
    parser.add_argument("--browser", default="patchright", choices=BROWSERS,
                        help="browser engine (default: patchright)")
    parser.add_argument("--headed", action="store_true", default=None,
                        help="show the browser window")
    parser.add_argument("--headless", action="store_true",
                        help="force headless (CF interstitial will fail)")
    args = parser.parse_args()

    wanted = select_targets(args.targets)
    needs_browser = any(t.runner_key in BROWSER_RUNNERS for t in wanted)
    has_interstitial = any(t.runner_key == "interstitial" for t in wanted)

    headed = args.headed or (not args.headless and has_interstitial)
    engine = args.browser

    mode = "headed" if headed else "headless"
    print(f"Running {len(wanted)} targets | browser: {engine} | mode: {mode}\n")

    rows: list[Row] = []
    ctx = _open_browser(engine, headed) if needs_browser else nullcontext(None)
    async with ctx as browser:
        for target in wanted:
            row = await run_target(target, browser, engine)
            rows.append(row)
            tag = "PASS" if row.result == "PASS" else "FAIL"
            print(f"  [{tag}] {row.target} ({row.bypass_s:.1f}s) {row.detail}")

    print()
    _print_table(rows)


def main() -> None:
    asyncio.run(amain())


if __name__ == "__main__":
    main()
