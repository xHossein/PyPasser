"""Slider-puzzle challenge solver (CV, no browser)."""

from __future__ import annotations

import io
from dataclasses import dataclass
from typing import Union

import numpy as np
from PIL import Image

_DARK_THRESHOLD = 95
_MAX_MEAN = 75.0
_MAX_STD = 20.0
_MIN_COMPONENT_PX = 150
_MIN_SIDE = 24
_MAX_SIDE = 140


@dataclass(frozen=True)
class PuzzleSolution:
    """Where to drop the piece."""

    x: int
    hole_left: int
    hole_top: int
    components: int


def _components(mask: np.ndarray) -> list[np.ndarray]:
    """8-connected components of a boolean mask (iterative flood fill)."""
    comps: list[np.ndarray] = []
    seen = np.zeros(mask.shape, dtype=bool)
    ys, xs = np.where(mask)
    for y0, x0 in zip(ys.tolist(), xs.tolist()):
        if seen[y0, x0]:
            continue
        seen[y0, x0] = True
        stack = [(y0, x0)]
        pts: list[tuple[int, int]] = []
        while stack:
            cy, cx = stack.pop()
            pts.append((cy, cx))
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    ny, nx = cy + dy, cx + dx
                    if (
                        0 <= ny < mask.shape[0]
                        and 0 <= nx < mask.shape[1]
                        and mask[ny, nx]
                        and not seen[ny, nx]
                    ):
                        seen[ny, nx] = True
                        stack.append((ny, nx))
        comps.append(np.asarray(pts, dtype=np.int64))
    return comps


def _alpha_bbox(piece: Image.Image) -> tuple[int, int, int, int]:
    """Bounding box (left, top, right, bottom) of the piece's visible pixels."""
    alpha = np.asarray(piece.convert("RGBA"))[:, :, 3]
    mask = alpha > 0
    if not mask.any():
        raise ValueError("piece has no visible pixels")
    ys, xs = np.where(mask)
    return int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())


def _candidates(
    background: Image.Image, expected_top: int | None = None
) -> list[tuple[int, int, int]]:
    """Plausible hole silhouettes as (left, top, pixel_count) tuples."""
    gray = np.asarray(background.convert("RGB")).astype(np.float64).mean(axis=2)
    stages = (
        (_DARK_THRESHOLD, _MAX_MEAN, _MAX_STD),
        (_DARK_THRESHOLD, _MAX_MEAN, 38.0),
        (_DARK_THRESHOLD, _MAX_MEAN, 50.0),
        (115, 95.0, 50.0),
    )
    last_cands: list[tuple[int, int, int]] = []
    for thresh, max_mean, max_std in stages:
        out: list[tuple[int, int, int]] = []
        for comp in _components(gray < thresh):
            if len(comp) < _MIN_COMPONENT_PX:
                continue
            left, top = int(comp[:, 1].min()), int(comp[:, 0].min())
            right, bottom = int(comp[:, 1].max()), int(comp[:, 0].max())
            w, h = right - left + 1, bottom - top + 1
            if min(w, h) < _MIN_SIDE or max(w, h) > _MAX_SIDE:
                continue
            values = gray[comp[:, 0], comp[:, 1]]
            if values.mean() > max_mean or values.std() > max_std:
                continue
            out.append((left, top, len(comp)))
        if out:
            last_cands = out
            if expected_top is None:
                return out
            if any(abs(cand[1] - expected_top) <= 12 for cand in out):
                return out
    return last_cands


def solve_puzzle(
    background: Union[Image.Image, bytes],
    piece: Union[Image.Image, bytes],
    y: int,
) -> PuzzleSolution:
    """Return the drop x for a puzzle challenge.

    Parameters
    ----------
    background: PIL image or bytes
        The background PNG (with the hole).
    piece: PIL image or bytes
        The piece PNG (semi-transparent).
    y: int
        ``content.y`` from the create response — the locked drag row.
    """
    if isinstance(background, bytes):
        background = Image.open(io.BytesIO(background))
    if isinstance(piece, bytes):
        piece = Image.open(io.BytesIO(piece))

    alpha_left, alpha_top, _, _ = _alpha_bbox(piece)
    cands = _candidates(background, expected_top=y + alpha_top)
    if not cands:
        raise ValueError("no hole silhouette found in background")

    def err(cand: tuple[int, int, int]) -> tuple[int, int]:
        return (abs((cand[1] - alpha_top) - y), -cand[2])

    cands.sort(key=err)
    hole_left, hole_top, _ = cands[0]
    return PuzzleSolution(
        x=hole_left - alpha_left,
        hole_left=hole_left,
        hole_top=hole_top,
        components=len(cands),
    )
