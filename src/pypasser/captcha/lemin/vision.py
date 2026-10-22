"""Piece/hole detection for the Lemin cropped captcha."""

from __future__ import annotations

from typing import NamedTuple

import numpy as np

from pypasser.captcha.lemin.constants import (
    GRID,
    PIECE_MARGIN,
    SCENE_WIDTH,
    WHITE_THRESHOLD,
)
from pypasser.vision import correlate_valid, sobel_magnitude

SILHOUETTE_ALPHA = 128
#: Weight of the marker's interior edge energy in the contour score.
_INTERIOR_PENALTY = 0.35
#: Ridge size, in pixels, of the interior mask used by the contour score.
_INTERIOR_EROSION = 4
_ROW_CHUNK = 32


class SilhouetteInfo(NamedTuple):
    """Piece silhouette mask and where it sits in the image."""

    mask: np.ndarray
    height: int
    width: int
    origin_x: int
    origin_y: int
    piece_ox: int
    piece_oy: int


def _box_sum(mask: np.ndarray, height: int, width: int) -> np.ndarray:
    """Sum of *mask* over every *height* x *width* window (valid positions).

    Returns an array of shape ``(H - height + 1, W - width + 1)`` where entry
    ``(y, x)`` covers ``mask[y:y+height, x:x+width]``.
    """
    padded = np.zeros((mask.shape[0] + 1, mask.shape[1] + 1), np.int32)
    padded[1:, 1:] = mask.cumsum(axis=0).cumsum(axis=1)
    return (
        padded[height:, width:]
        - padded[:-height, width:]
        - padded[height:, :-width]
        + padded[:-height, :-width]
    )


def _coverage_scorer(mask: np.ndarray, silhouette: np.ndarray):
    """Function scoring a placement by coverage minus unexplained white."""
    sil_rows = np.flatnonzero(silhouette.any(axis=1))
    shifts: list[tuple[int, np.ndarray]] = []
    for row in sil_rows:
        cols = np.flatnonzero(silhouette[row])
        shifts.append((int(row), cols))
    sil_area = float(silhouette.sum())

    def coverage(hy: int, hx: int) -> tuple[float, int]:
        hit = 0
        for row, cols in shifts:
            hit += int(mask[hy + row, hx + cols].sum())
        return hit / sil_area, hit

    return coverage, shifts, sil_area


def silhouette(image: np.ndarray, scene_width: int = SCENE_WIDTH) -> SilhouetteInfo:
    """Piece silhouette mask and where it sits in the image."""
    strip = image[:, scene_width:, 3]
    ys, xs = np.where(strip > SILHOUETTE_ALPHA)
    if not ys.size:
        raise ValueError("no piece silhouette in the image strip")
    x0, x1 = int(xs.min()), int(xs.max())
    y0, y1 = int(ys.min()), int(ys.max())
    mask = strip[y0:y1 + 1, x0:x1 + 1] > SILHOUETTE_ALPHA
    piece_ox = (scene_width + x0) - (scene_width + PIECE_MARGIN)
    piece_oy = y0 - PIECE_MARGIN
    return SilhouetteInfo(
        mask=mask,
        height=y1 - y0 + 1,
        width=x1 - x0 + 1,
        origin_x=scene_width + x0,
        origin_y=y0,
        piece_ox=piece_ox,
        piece_oy=piece_oy,
    )


def _edge_magnitude(scene: np.ndarray) -> np.ndarray:
    """Sobel gradient magnitude of the scene, collapsed to luminance."""
    return sobel_magnitude(scene.mean(axis=2))


def _boundary_masks(mask: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Silhouette outline and its shrunken interior, as float weights."""
    def erode(m: np.ndarray) -> np.ndarray:
        p = np.pad(m, 1, constant_values=False)
        return (
            m
            & p[2:, 1:-1]
            & p[:-2, 1:-1]
            & p[1:-1, 2:]
            & p[1:-1, :-2]
        )

    outline = mask & ~erode(mask)
    interior = mask.copy()
    for _ in range(_INTERIOR_EROSION):
        interior = erode(interior)
    return outline.astype(np.float64), interior.astype(np.float64)


def _grid_top_n(
    scores: np.ndarray,
    piece_ox: int,
    piece_oy: int,
    sh: int,
    sw: int,
    grid: int,
    top_n: int,
    min_score: float | None = None,
) -> list[tuple[float, int, int]]:
    """Pick the *top_n* highest-scoring grid-aligned positions with NMS.

    Returns ``(score, x, y)`` triples, best first, where positions closer than
    half the silhouette size are suppressed.
    """
    rows = np.flatnonzero((np.arange(scores.shape[0]) - piece_oy) % grid == 0)
    cols = np.flatnonzero((np.arange(scores.shape[1]) - piece_ox) % grid == 0)
    if not rows.size or not cols.size:
        return []

    grid_scores = scores[np.ix_(rows, cols)]
    order = np.argsort(grid_scores, axis=None)[::-1]
    picked: list[tuple[float, int, int]] = []
    for flat in order:
        i, j = np.unravel_index(int(flat), grid_scores.shape)
        val = float(grid_scores[i, j])
        if min_score is not None and val < min_score:
            break
        hx, hy = int(cols[j]), int(rows[i])
        if all(
            abs(hx - px) > sw // 2 or abs(hy - py) > sh // 2
            for _, px, py in picked
        ):
            picked.append((val, hx, hy))
        if len(picked) >= top_n:
            break
    return picked


def find_slot_by_contour(
    image: np.ndarray,
    scene_width: int = SCENE_WIDTH,
    grid: int = GRID,
    top_n: int = 3,
) -> list[tuple[float, int, int]]:
    """Rank grid-aligned placements by jigsaw-contour sharpness.

    Returns up to *top_n* ``(score, x, y)`` triples, best first, with
    ``x``/``y`` the silhouette's top-left corner in natural scene pixels.
    """
    sil = silhouette(image, scene_width)
    edges = _edge_magnitude(image[:, :scene_width, :3])
    outline, interior = _boundary_masks(sil.mask)
    if not outline.any() or not interior.any():
        return []

    scores = correlate_valid(edges, outline) - _INTERIOR_PENALTY * correlate_valid(
        edges, interior
    )
    return _grid_top_n(
        scores, sil.piece_ox, sil.piece_oy, sil.height, sil.width, grid, top_n,
    )


def find_hole(
    image: np.ndarray,
    scene_width: int = SCENE_WIDTH,
    grid: int = GRID,
    top_n: int = 3,
    white_threshold: int = WHITE_THRESHOLD,
) -> list[tuple[float, int, int]]:
    """Rank grid-aligned placements of the piece silhouette in the scene.

    Returns up to *top_n* ``(score, x, y)`` triples, best first, where ``x``
    and ``y`` are the silhouette's top-left corner in natural scene pixels.
    """
    sil = silhouette(image, scene_width)
    scene = image[:, :scene_width, :3]
    white = scene.min(axis=2) >= white_threshold
    white_area = int(white.sum())
    if white_area < max(40, int(sil.mask.sum() * 0.25)):
        return []

    window = _box_sum(white, sil.height, sil.width)
    coverage, _, sil_area = _coverage_scorer(white, sil.mask)

    # Score each candidate position via exact pixel coverage.
    rows = np.flatnonzero((np.arange(window.shape[0]) - sil.piece_oy) % grid == 0)
    cols = np.flatnonzero((np.arange(window.shape[1]) - sil.piece_ox) % grid == 0)
    if not rows.size or not cols.size:
        return []

    score_map = np.full(window.shape, -np.inf)
    for start in range(0, rows.size, _ROW_CHUNK):
        block = rows[start:start + _ROW_CHUNK]
        covered = window[np.ix_(block, cols)]
        candidates = np.argwhere(covered >= max(6, int(sil_area * 0.2)))
        for i, j in candidates:
            hy, hx = int(block[i]), int(cols[j])
            cover, hit = coverage(hy, hx)
            uncovered = int(covered[i, j]) - hit
            score_map[hy, hx] = cover - uncovered / float(max(1, white_area))

    return _grid_top_n(
        score_map, sil.piece_ox, sil.piece_oy,
        sil.height, sil.width, grid, top_n, min_score=0.05,
    )


def destination(
    slot: tuple[int, int],
    piece_ox: int,
    piece_oy: int,
    grid: int = GRID,
) -> tuple[int, int]:
    """Silhouette top-left -> piece wrapper ``left``/``top`` in natural pixels."""
    from pypasser.captcha.lemin.answers import js_round

    left = js_round((slot[0] - piece_ox) / grid) * grid
    top = js_round((slot[1] - piece_oy) / grid) * grid
    return left, top


def solve_image(
    image: np.ndarray,
    scene_width: int = SCENE_WIDTH,
    grid: int = GRID,
) -> tuple[int, int]:
    """Best destination ``(left, top)`` for a cropped scene image."""
    sil = silhouette(image, scene_width)
    holes = find_slot_by_contour(image, scene_width, grid) or find_hole(
        image, scene_width, grid
    )
    if not holes:
        raise ValueError("no candidate slot found in the scene")
    return destination((holes[0][1], holes[0][2]), sil.piece_ox, sil.piece_oy, grid)
