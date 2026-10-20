"""Computer-vision primitives shared by image-based solvers.

``pip install PyPasser[vision]``
"""

from __future__ import annotations

from pypasser.vision.edges import canny
from pypasser.vision.match import best_match, best_match_in_band, score_map

__all__ = ["best_match", "best_match_in_band", "canny", "score_map"]
