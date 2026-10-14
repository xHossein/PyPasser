from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SolverResult:
    """Result returned by every PyPasser solver.

    Attributes
    ----------
    is_solved: bool
        Whether the challenge was solved. For reCaptcha V3 solvers this is
        always ``True`` when a result is returned (failures raise instead).
    response_token: str or None
        The ``g-recaptcha-response`` token. For V3 HTTP mode this is the
        ``rresp`` token; for V3 page mode it is read from the page; for V2 it
        is the value of the ``#g-recaptcha-response`` textarea. For Cloudflare
        Turnstile it is the ``cf-turnstile-response`` value (``None`` on the
        interstitial path, where the page navigates away and the token is
        gone).
    cookies: dict or None
        Cookies proving a cleared session, ``name -> value``. The Turnstile
        solver sets it from the browser context after a full-page Cloudflare
        challenge (it then contains ``cf_clearance``), and the ArvanCloud
        bypass sets it with the decoded ``__arcsjs`` / ``__arcsjsc`` pair —
        so a plain HTTP client can replay either cleared session (see the
        interstitial example). ``None`` when the solver produced no cookies.
    user_agent: str or None
        The ``navigator.userAgent`` of the browser that solved the challenge,
        when known. Cloudflare ties ``cf_clearance`` to the visitor's device,
        so an HTTP client replaying that cookie must send the same UA — as
        must the client replaying ArvanCloud clearance cookies.
    """

    is_solved: bool
    response_token: str | None = None
    cookies: dict[str, str] | None = None
    user_agent: str | None = None
