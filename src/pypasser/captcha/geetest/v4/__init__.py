"""GeeTest V4 captcha solver.

Usage::

    from pypasser.captcha import geetest

    res = geetest.v4.solve("CAPTCHA_ID")              # detect the type, best method
    res = await geetest.v4.asolve("CAPTCHA_ID", risk_type="ai")

    seccode = json.loads(res.response_token)          # the widget's seccode

``response_token`` is the ``seccode`` object serialized as JSON, because
GeeTest submits a structured object (``captcha_id``, ``lot_number``,
``pass_token``, ``gen_time``, ``captcha_output``) rather than a single string.

By default the captcha id alone is enough: the solver asks ``/load`` for the
configured type and chooses a strategy. ``slide``, ``ai``, ``winlinze``,
``match``, ``svg_icon`` and ``voice`` and ... are supported; the first four use their
own bypass method first, ``nine`` and ``icon`` use the audio fallback only, and
``svg_icon`` prefers audio with its keyframe sweep as fallback.

    pip install PyPasser[vision]
    pip install PyPasser[speech]
"""

from __future__ import annotations

import json
from typing import Optional, Union

from pypasser.captcha.geetest.v4.asolver import AsyncGeeTestV4Solver
from pypasser.captcha.geetest.v4.protocol.constants import DEFAULT_LANG, DEFAULT_UA
from pypasser.captcha.geetest.v4.solver import SUPPORTED_RISK_TYPES, GeeTestV4Solver
from pypasser.structs import SolverResult

__all__ = [
    "solve",
    "asolve",
    "GeeTestV4Solver",
    "AsyncGeeTestV4Solver",
    "SUPPORTED_RISK_TYPES",
]


def solve(
    captcha_id: str,
    *,
    risk_type: str = "auto",
    proxy: Optional[str] = None,
    timeout: Union[int, float] = 20,
    lang: str = DEFAULT_LANG,
    user_agent: str = DEFAULT_UA,
    attempts: int = 3,
    voice_model_path: Optional[str] = None,
) -> SolverResult:
    """Solve a GeeTest V4 challenge and return a :class:`SolverResult`.

    Parameters
    ----------
    captcha_id: str
        The site's GeeTest V4 captcha id.
    risk_type: str
        ``"auto"`` (default) asks the server which type the captcha id serves
        and picks the best answering strategy for it. Override with
        ``"slide"``, ``"ai"``, ``"winlinze"``, ``"match"``, ``"svg_icon"``,
        ``"nine"``, ``"icon"`` or ``"voice"``.
    proxy: str, optional
        Proxy URL, e.g. ``"socks5://user:pass@host:port"``.
    timeout: int or float
        Per-request timeout in seconds.
    lang: str
        Language sent to ``/load``.
    user_agent: str
        User agent for every request.
    attempts: int
        Attempts before giving up.
    voice_model_path: str, optional
        Directory of the Vosk speech model used by ``risk_type="voice"``.
        Vosk's own default is used when omitted.
    """
    seccode = GeeTestV4Solver(
        captcha_id,
        risk_type=risk_type,
        proxy=proxy,
        timeout=timeout,
        lang=lang,
        user_agent=user_agent,
        voice_model_path=voice_model_path,
    ).solve(attempts=attempts)
    return SolverResult(is_solved=True, response_token=json.dumps(seccode))


async def asolve(
    captcha_id: str,
    *,
    risk_type: str = "auto",
    proxy: Optional[str] = None,
    timeout: Union[int, float] = 20,
    lang: str = DEFAULT_LANG,
    user_agent: str = DEFAULT_UA,
    attempts: int = 3,
    voice_model_path: Optional[str] = None,
) -> SolverResult:
    """Async version of :func:`solve`."""
    seccode = await AsyncGeeTestV4Solver(
        captcha_id,
        risk_type=risk_type,
        proxy=proxy,
        timeout=timeout,
        lang=lang,
        user_agent=user_agent,
        voice_model_path=voice_model_path,
    ).solve(attempts=attempts)
    return SolverResult(is_solved=True, response_token=json.dumps(seccode))
