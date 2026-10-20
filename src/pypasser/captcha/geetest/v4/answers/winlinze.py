"""Board logic for the GeeTest V4 ``winlinze``."""

from __future__ import annotations

from typing import List, Optional, Sequence, Tuple

from pypasser.exceptions import GeeTestSolveFailed

Cell = Tuple[int, int]
Board = Sequence[Sequence[int]]

# A cell carries one of these tokens; 0 means empty.
_EMPTY = 0


def _lines(size: int) -> List[List[Cell]]:
    """Every full-length row, column and both main diagonals."""
    rows = [[(r, c) for c in range(size)] for r in range(size)]
    cols = [list(column) for column in zip(*rows)]
    down = [(i, i) for i in range(size)]
    up = [(i, size - 1 - i) for i in range(size)]
    return rows + cols + [down, up]


def _complete_line(board: Board, line: Sequence[Cell]) -> Optional[Tuple[int, Cell]]:
    """``(token, empty_cell)`` if this line is four-of-a-kind plus one empty."""
    values = [board[r][c] for r, c in line]
    if values.count(_EMPTY) != 1:
        return None
    filled = [value for value in values if value != _EMPTY]
    if len(set(filled)) != 1:
        return None
    return filled[0], line[values.index(_EMPTY)]


def _removable(board: Board, token: int, line: Sequence[Cell]) -> Optional[Cell]:
    """A cell holding ``token`` outside ``line`` — the token that moves."""
    on_line = set(line)
    for r in range(len(board)):
        for c in range(len(board)):
            if (r, c) not in on_line and board[r][c] == token:
                return r, c
    return None


def solve_board(board: Board) -> List[List[int]]:
    """Return ``[[remove_row, remove_col], [fill_row, fill_col]]``.

    Parameters
    ----------
    board:
        The ``ques`` matrix from ``/load``.
    """
    size = len(board)
    if size == 0 or any(len(row) != size for row in board):
        raise GeeTestSolveFailed(f"winlinze board is not square: {board!r}")

    matches: List[Tuple[int, Cell, Cell]] = []
    for line in _lines(size):
        completed = _complete_line(board, line)
        if completed is None:
            continue
        token, fill = completed
        remove = _removable(board, token, line)
        if remove is not None:
            matches.append((token, remove, fill))

    if not matches:
        raise GeeTestSolveFailed(
            f"winlinze board has no line of four with an empty cell: {board!r}"
        )
    if len({fill for _, _, fill in matches}) > 1:
        raise GeeTestSolveFailed(
            f"winlinze board is ambiguous, {len(matches)} completing lines: {board!r}"
        )

    _, remove, fill = matches[0]
    return [[remove[0], remove[1]], [fill[0], fill[1]]]


def answer_fields(board: Board) -> dict:
    """The ``userresponse`` payload fragment for a winlinze challenge."""
    return {"userresponse": solve_board(board)}


__all__ = ["answer_fields", "solve_board"]
