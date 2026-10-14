"""PyPasser — captcha and anti-bot solvers.

Two namespaces, split by what a solver produces:

``pypasser.captcha``
    Widget solvers. They return a *token* you submit with your request.

``pypasser.antibot``
    Site-gating bot walls (the full-page "checking your browser" interstitials).
    They return *clearance cookies* plus the User-Agent they are bound to, so a
    plain HTTP client can replay the cleared session.

Usage::

    from pypasser import SolverResult
    from pypasser.captcha import arcaptcha, recaptcha, turnstile
    from pypasser.antibot import arvancloud, cloudflare

    # reCaptcha
    res = recaptcha.v3.solve("https://www.google.com/recaptcha/api2/anchor?ar=1&k=...&co=...")
    res = recaptcha.v2.solve(playwright_page)
    res = await recaptcha.v2.asolve(async_playwright_page)

    # captcha widgets
    res = turnstile.solve(playwright_page)
    res = arcaptcha.solve("SITE_KEY", domain="example.ir")

    # anti-bot walls (clearance cookies for HTTP replay)
    res = cloudflare.solve(playwright_page)
    res = arvancloud.solve("https://example.ir/protected")
    res = await arvancloud.asolve("https://example.ir/protected")

Every solver has a sync (``solve``) and an async (``asolve``) counterpart
sharing the same arguments, and every solver returns a
:class:`~pypasser.structs.SolverResult`.
"""

from pypasser.structs import SolverResult

from . import antibot, captcha

__version__ = "1.0.0"

__all__ = ["antibot", "captcha", "SolverResult", "__version__"]
