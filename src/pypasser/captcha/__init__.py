"""Captcha widget solvers — each returns a token."""

from . import arcaptcha, recaptcha, turnstile

__all__ = ["arcaptcha", "recaptcha", "turnstile"]
