"""Answer strategies, one module per GeeTest risk type."""

from __future__ import annotations

from typing import Any, Optional

from pypasser.captcha.geetest.v4.answers import (
    match,
    slide,
    svg_icon,
    voice,
    winlinze,
)
from pypasser.captcha.geetest.v4.protocol.transport import require_data
from pypasser.exceptions import GeeTestSolveFailed


def fields(
    risk_type: str,
    data: dict[str, Any],
    images: dict[str, bytes],
    voice_model_path: Optional[str] = None,
) -> dict[str, Any]:
    """The risk_type-specific part of the verify payload."""
    if risk_type == "ai":
        # The AI challenge carries no answer; the signature is the answer.
        return {}
    if risk_type == "winlinze":
        require_data(data, "ques")
        return winlinze.answer_fields(data["ques"])
    if risk_type == "match":
        require_data(data, "ques")
        return match.answer_fields(data["ques"])
    if risk_type == "voice":
        return voice.answer_fields(images["voice"], voice_model_path)
    if risk_type == "slide":
        return slide.answer_fields(images["bg"], images["slice"], int(data["ypos"]))
    raise GeeTestSolveFailed(
        f"risk type {risk_type!r} answers with trials, not a single payload"
    )


__all__ = ["fields", "match", "slide", "svg_icon", "voice", "winlinze"]
