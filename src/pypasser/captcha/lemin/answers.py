"""Answer-string construction for the Lemin cropped captcha.

The widget records a drag as a token history. Each mouse move appends::

    <piece index>x<left>x<top>x

with ``left``/``top`` the piece wrapper position divided by the scale and
rendered in base 32, and the history truncated to the last 300 tokens. The
submitted ``answer`` is that history joined with ``x``.

The server accepts a path of at least :data:`MIN_POINTS` points whose *last*
point is the correct destination. Intermediate points are barely checked — a
300 px jump, a duplicate, or a start far from the piece's home all pass — but
a path of interior points scattered at random does not, which is what a
monotone drag reproduces for free.
"""

from __future__ import annotations

import random
from typing import Iterable, Sequence

from pypasser.captcha.lemin.constants import (
    B32_ALPHABET,
    GRID,
    HOME,
    MIN_POINTS,
)

Point = tuple[int, int]


def js_round(value: float) -> int:
    """``Math.round`` semantics (half away from zero for positives)."""
    return int(value + 0.5)


def b32(value: int) -> str:
    """Base-32 encode the way ``Number.prototype.toString(32)`` does."""
    if value < 0:
        return "-" + b32(-value)
    if value == 0:
        return "0"
    out = ""
    while value:
        value, digit = divmod(value, 32)
        out = B32_ALPHABET[digit] + out
    return out


def token(index: int, left: int, top: int) -> str:
    """One ``<index>x<left>x<top>x`` answer token."""
    return f"{b32(index)}x{b32(left)}x{b32(top)}x"


def encode(points: Sequence[Point], index: int = 0) -> str:
    """Encode a path as the ``answer`` value sent to ``pre-validate``."""
    return "".join(token(index, x, y) for x, y in points)


def snap(value: float, grid: int = GRID) -> int:
    """Snap a natural-pixel coordinate onto the drag grid."""
    return js_round(value / grid) * grid


def drag_path(
    destination: Point,
    *,
    home: Point = HOME,
    points: int = 30,
    jitter: float = 0.0,
    rng: random.Random | None = None,
) -> list[Point]:
    """A grid-snapped straight drag from *home* to *destination*."""
    rng = rng or random.Random()
    steps: list[Point] = []
    for k in range(1, points + 1):
        nx = home[0] + (destination[0] - home[0]) * k / points
        ny = home[1] + (destination[1] - home[1]) * k / points
        if jitter:
            nx += rng.uniform(-jitter, jitter)
            ny += rng.uniform(-jitter, jitter)
        point = (snap(nx), snap(ny))
        if not steps or steps[-1] != point:
            steps.append(point)
    return _pad_to_minimum(steps, home)


def _pad_to_minimum(steps: list[Point], home: Point) -> list[Point]:
    if len(steps) >= MIN_POINTS:
        return steps
    floor = MIN_POINTS - len(steps)
    return [home] * floor + steps


def multi_drag_path(
    destinations: Iterable[Point],
    *,
    home: Point = HOME,
    points_per_piece: int = 30,
    rng: random.Random | None = None,
) -> list[Point]:
    """Path for a challenge with more than one piece."""
    rng = rng or random.Random()
    path: list[Point] = []
    previous = home
    for destination in destinations:
        leg = drag_path(
            destination, home=previous, points=points_per_piece, rng=rng
        )
        path.extend(leg)
        previous = destination
    return path
