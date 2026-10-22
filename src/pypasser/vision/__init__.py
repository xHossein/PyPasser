"""Computer-vision primitives shared by image-based solvers.

``pip install PyPasser[vision]``
"""

from __future__ import annotations

from pypasser.vision.edges import canny, sobel_magnitude
from pypasser.vision.match import (
    best_match,
    best_match_in_band,
    correlate_valid,
    score_map,
)

__all__ = [
    "best_match",
    "best_match_in_band",
    "canny",
    "correlate_valid",
    "score_map",
    "sobel_magnitude",
]
