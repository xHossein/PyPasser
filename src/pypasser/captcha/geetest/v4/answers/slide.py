"""Slider-puzzle CV for GeeTest V4."""

from __future__ import annotations

import io
import random

from pypasser.exceptions import GeeTestSolveFailed

# userresponse = left / scale + offset, as the widget computes it.
_USER_RESPONSE_SCALE = 1.0059466666666665
_USER_RESPONSE_OFFSET = 2

# How many rows around the server-declared piece row to accept a match in.
_ROW_TOLERANCE = 2


def _to_gray(raw: bytes):
    import numpy as np
    from PIL import Image

    return np.asarray(Image.open(io.BytesIO(raw)).convert("L"))


def piece_left(background_png: bytes, piece_png: bytes, ypos: int) -> tuple[int, float]:
    """Locate the piece; return ``(left, score)``.

    Parameters
    ----------
    background_png: bytes
        The background image, with the hole.
    piece_png: bytes
        The slider piece image.
    ypos: int
        ``ypos`` from ``/load`` — the row the piece belongs on.
    """
    try:
        from pypasser.vision import best_match, best_match_in_band, canny, score_map

        background = _to_gray(background_png)
        piece = _to_gray(piece_png)
    except ImportError as exc:
        raise GeeTestSolveFailed(
            "slide challenges need the 'vision' extra: pip install PyPasser[vision]"
        ) from exc
    except Exception as exc:  # malformed image
        raise GeeTestSolveFailed(f"could not decode slide images: {exc}") from exc

    background_edges = canny(background)
    piece_edges = canny(piece)
    if not piece_edges.any():
        raise GeeTestSolveFailed("piece image has no detectable edges")

    scores = score_map(background_edges, piece_edges)
    x, y, score = best_match_in_band(scores, int(ypos), _ROW_TOLERANCE)
    if score <= 0:
        # The banded peak is weaker than no-correlation; fall back to global.
        x, y, score = best_match(background_edges, piece_edges)
    return x - 1, score


def user_response(left: int) -> float:
    """The ``userresponse`` the widget sends for a given ``left``."""
    return left / _USER_RESPONSE_SCALE + _USER_RESPONSE_OFFSET


def answer_fields(background_png: bytes, piece_png: bytes, ypos: int) -> dict:
    """The slider payload fragment for a slide challenge."""
    left, _score = piece_left(background_png, piece_png, ypos)
    return {
        "passtime": random.randint(600, 1200),
        "setLeft": left,
        "userresponse": user_response(left),
    }


__all__ = ["answer_fields", "piece_left", "user_response"]
