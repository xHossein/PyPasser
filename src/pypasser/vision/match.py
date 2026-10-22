"""Template matching.

Zero-mean normalized cross-correlation, equivalent to OpenCV's
``TM_CCOEFF_NORMED``.
"""

from __future__ import annotations

import numpy as np


def correlate_valid(img: np.ndarray, kernel: np.ndarray) -> np.ndarray:
    """Cross-correlation of ``img`` with ``kernel``, keeping valid positions."""
    h, w = img.shape
    kh, kw = kernel.shape
    shape = (h + kh - 1, w + kw - 1)
    fa = np.fft.rfft2(img, s=shape)
    fb = np.fft.rfft2(kernel[::-1, ::-1], s=shape)
    full = np.fft.irfft2(fa * fb, s=shape)
    return full[kh - 1:h, kw - 1:w]


_correlate_valid = correlate_valid


def score_map(image: np.ndarray, template: np.ndarray) -> np.ndarray:
    """Normalized cross-correlation of ``template`` over ``image``.

    Parameters
    ----------
    image: ndarray
        The scene to search (typically an edge map).
    template: ndarray
        The pattern to find; must be no larger than ``image``.

    Returns
    -------
    ndarray
        Scores in ``[-1, 1]``, shaped so that ``out[y, x]`` is the score of
        the window whose top-left corner sits at ``(y, x)``.
    """
    if template.shape[0] > image.shape[0] or template.shape[1] > image.shape[1]:
        raise ValueError("template is larger than the image")

    img = image.astype(np.float64)
    tmpl = template.astype(np.float64)
    n = tmpl.size

    centered = tmpl - tmpl.mean()
    ones = np.ones_like(tmpl)
    numerator = _correlate_valid(img, centered)
    sum_img = _correlate_valid(img, ones)
    sum_img_sq = _correlate_valid(img * img, ones)

    variance = sum_img_sq - sum_img * sum_img / n
    denominator = np.sqrt(np.maximum(variance, 1e-9) * (centered * centered).sum())
    return numerator / denominator


def best_match(image: np.ndarray, template: np.ndarray) -> tuple[int, int, float]:
    """Top-left corner and score of the best match."""
    scores = score_map(image, template)
    y, x = np.unravel_index(int(np.argmax(scores)), scores.shape)
    return int(x), int(y), float(scores[y, x])


def best_match_in_band(
    scores: np.ndarray, center_row: int, tolerance: int
) -> tuple[int, int, float]:
    """Best match restricted to ``center_row +- tolerance`` rows.

    Constraining the search to the row the server says the piece belongs on
    recovers matches that a global peak loses to background texture.
    """
    rows = scores.shape[0]
    lo = max(0, center_row - tolerance)
    hi = min(rows, center_row + tolerance + 1)
    if lo >= hi:
        lo, hi = 0, rows
    band = scores[lo:hi]
    y, x = np.unravel_index(int(np.argmax(band)), band.shape)
    return int(x), int(y + lo), float(band[y, x])


__all__ = ["best_match", "best_match_in_band", "correlate_valid", "score_map"]
