"""Anti-bot solvers for site-gating bot walls.

Solvers::

    from pypasser.antibot import arvancloud, cloudflare

    res = cloudflare.solve(playwright_page)                # cf_clearance
    res = arvancloud.solve("https://example.ir/protected")  # __arcsjs cookies
"""

from . import arvancloud, cloudflare

__all__ = ["arvancloud", "cloudflare"]
