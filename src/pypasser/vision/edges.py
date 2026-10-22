"""Edge detection.

Canny Algorithm: Gaussian blur -> Sobel gradients -> non-maximum suppression ->
double threshold with hysteresis.

.. note::
   ``blur=0`` reproduces ``OpenCV's Canny`` style.
"""

from __future__ import annotations

import numpy as np

_DEFAULT_LOW = 100
_DEFAULT_HIGH = 200


def _gaussian(img: np.ndarray, size: int) -> np.ndarray:
    """Separable Gaussian blur; ``size`` of 0, 3 or 5 (0 returns the input)."""
    if size == 0:
        return img
    kernels = {
        3: np.array([0.25, 0.5, 0.25]),
        5: np.array([1.0, 4.0, 6.0, 4.0, 1.0]) / 16.0,
    }
    kernel = kernels.get(size)
    if kernel is None:
        raise ValueError("gaussian size must be 0, 3 or 5")

    radius = len(kernel) // 2
    padded = np.pad(img, radius, mode="reflect")
    rows = np.zeros_like(img)
    for i, weight in enumerate(kernel):
        rows += weight * padded[radius:radius + img.shape[0], i:i + img.shape[1]]

    padded = np.pad(rows, radius, mode="reflect")
    out = np.zeros_like(img)
    for i, weight in enumerate(kernel):
        out += weight * padded[i:i + img.shape[0], radius:radius + img.shape[1]]
    return out


def _sobel(img: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """3x3 Sobel gradients (Gx, Gy) with reflected borders."""
    p = np.pad(img, 1, mode="reflect")
    gx = (-p[:-2, :-2] + p[:-2, 2:]
          - 2 * p[1:-1, :-2] + 2 * p[1:-1, 2:]
          - p[2:, :-2] + p[2:, 2:])
    gy = (-p[:-2, :-2] - 2 * p[:-2, 1:-1] - p[:-2, 2:]
          + p[2:, :-2] + 2 * p[2:, 1:-1] + p[2:, 2:])
    return gx, gy


def sobel_magnitude(gray: np.ndarray) -> np.ndarray:
    """Gradient magnitude of a 2-D array (3x3 Sobel, Euclidean norm)."""
    gx, gy = _sobel(np.asarray(gray, dtype=np.float64))
    return np.hypot(gx, gy)


def _dilate(mask: np.ndarray) -> np.ndarray:
    """3x3 binary dilation by shifting (no scipy)."""
    out = mask.copy()
    out[1:, :] |= mask[:-1, :]
    out[:-1, :] |= mask[1:, :]
    out[:, 1:] |= mask[:, :-1]
    out[:, :-1] |= mask[:, 1:]
    out[1:, 1:] |= mask[:-1, :-1]
    out[:-1, :-1] |= mask[1:, 1:]
    out[1:, :-1] |= mask[:-1, 1:]
    out[:-1, 1:] |= mask[1:, :-1]
    return out


def _non_max_suppression(mag: np.ndarray, angle: np.ndarray) -> np.ndarray:
    """Thin ridges to 1px, comparing against neighbours along the gradient."""
    m = mag
    left, right = np.roll(m, 1, 1), np.roll(m, -1, 1)
    up, down = np.roll(m, 1, 0), np.roll(m, -1, 0)
    ul = np.roll(np.roll(m, 1, 0), 1, 1)
    dr = np.roll(np.roll(m, -1, 0), -1, 1)
    ur = np.roll(np.roll(m, 1, 0), -1, 1)
    dl = np.roll(np.roll(m, -1, 0), 1, 1)

    d0 = (angle < 22.5) | (angle >= 157.5)
    d45 = (angle >= 22.5) & (angle < 67.5)
    d90 = (angle >= 67.5) & (angle < 112.5)
    d135 = (angle >= 112.5) & (angle < 157.5)

    keep = (d0 & (m >= left) & (m >= right))
    keep |= d45 & (m >= ul) & (m >= dr)
    keep |= d90 & (m >= up) & (m >= down)
    keep |= d135 & (m >= ur) & (m >= dl)
    return np.where(keep, m, 0.0)


def canny(
    gray: np.ndarray,
    low: int = _DEFAULT_LOW,
    high: int = _DEFAULT_HIGH,
    blur: int = 0,
) -> np.ndarray:
    """Canny edges of a 2-D grayscale array; returns a uint8 0/255 map."""
    img = _gaussian(np.asarray(gray, dtype=np.float64), blur)
    gx, gy = _sobel(img)

    mag = np.abs(gx) + np.abs(gy)
    angle = (np.rad2deg(np.arctan2(gy, gx)) + 180.0) % 180.0
    thin = _non_max_suppression(mag, angle)

    strong = thin > high
    weak = thin > low
    edges = strong.copy()
    for _ in range(int(max(thin.shape))):
        grown = _dilate(edges) & weak
        if np.array_equal(grown, edges):
            break
        edges = grown
    return (edges * 255).astype(np.uint8)


__all__ = ["canny", "sobel_magnitude"]
