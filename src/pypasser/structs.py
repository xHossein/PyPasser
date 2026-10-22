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
    response_token: str or dict or None
        The solver's response token(s).  For reCaptcha this is the
        ``g-recaptcha-response`` string; for Cloudflare Turnstile it is
        ``cf-turnstile-response``; for GeeTest v4 it is the JSON-encoded
        ``seccode`` dict.  For Lemin it is a dict with keys ``pv_token``,
        ``answer``, and ``challenge_id`` — browser-automation users can
        inject ``answer`` and ``challenge_id`` into the widget's hidden
        ``lemin_answer`` / ``lemin_challenge_id`` inputs to mark the
        challenge as solved.
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
    response_token: str | dict[str, str] | None = None
    cookies: dict[str, str] | None = None
    user_agent: str | None = None
