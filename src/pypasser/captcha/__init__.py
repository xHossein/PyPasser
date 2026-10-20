"""Captcha widget solvers — each returns a token."""

from . import arcaptcha, geetest, recaptcha, turnstile

__all__ = ["arcaptcha", "geetest", "recaptcha", "turnstile"]
