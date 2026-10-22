"""Captcha widget solvers — each returns a token."""

from . import arcaptcha, geetest, lemin, recaptcha, turnstile

__all__ = ["arcaptcha", "geetest", "lemin", "recaptcha", "turnstile"]
