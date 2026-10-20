"""Answer strategy for the GeeTest V4 ``svg_icon``."""

from __future__ import annotations

import re
from typing import List, Tuple

from pypasser.exceptions import GeeTestSolveFailed

FRAME_COUNT = 3
GRID = 2

_DURATION = re.compile(r"animation:\s*geetest_frame1_animation_hash\s+([\d.]+)s")
_MARK = re.compile(r"([\d.]+)% \{ opacity: (\d); \}")

Window = Tuple[float, float]


def frame_windows(svg: str) -> Tuple[List[Window], float]:
    """Return each frame's visible ``(start, end)`` percent and the cycle length.

    Raises :class:`GeeTestSolveFailed` if the SVG does not carry the expected
    keyframes, since a guessing strategy without them could not be timed.
    """
    match = _DURATION.search(svg)
    if match is None:
        raise GeeTestSolveFailed("svg_icon challenge has no frame animation")
    duration_ms = float(match.group(1)) * 1000

    windows: List[Window] = []
    for frame in range(1, FRAME_COUNT + 1):
        marker = f"@keyframes geetest_frame{frame}_animation_hash"
        start = svg.find(marker)
        if start == -1:
            raise GeeTestSolveFailed(
                f"svg_icon challenge has no keyframes for frame {frame}"
            )
        stop = svg.find("@", start + len(marker))
        block = svg[start : stop if stop != -1 else len(svg)]
        marks = [(float(p), int(v)) for p, v in _MARK.findall(block)]
        on = next((p for p, v in marks if v == 1), None)
        if on is None:
            raise GeeTestSolveFailed(f"svg_icon frame {frame} is never visible")
        off = next((p for p, v in marks if v == 0 and p > on), 100.0)
        windows.append((on, off))
    return windows, duration_ms


def passtime(windows: List[Window], duration_ms: float, frame: int) -> int:
    """A ``passtime`` that lands inside ``frame``'s visible window."""
    start, end = windows[frame]
    return max(1, int((start + end) / 200 * duration_ms))


def trials(svg: str) -> List[dict]:
    """Every ``{userresponse, passtime}`` candidate, frame by frame."""
    windows, duration_ms = frame_windows(svg)
    return [
        {
            "userresponse": [row, col],
            "passtime": passtime(windows, duration_ms, frame),
        }
        for frame in range(FRAME_COUNT)
        for row in range(1, GRID + 1)
        for col in range(1, GRID + 1)
    ]


__all__ = ["frame_windows", "passtime", "trials"]
