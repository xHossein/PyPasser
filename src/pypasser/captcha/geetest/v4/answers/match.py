"""Board logic for the GeeTest V4 ``match``."""

from __future__ import annotations

from typing import List, Sequence, Tuple

from pypasser.exceptions import GeeTestSolveFailed

Board = Sequence[Sequence[int]]
Cell = Tuple[int, int]


def _neighbours(size: int) -> List[Tuple[Cell, Cell]]:
    """Every pair of sideways-touching cells, each pair once."""
    pairs: List[Tuple[Cell, Cell]] = []
    for column in range(size):
        for row in range(size):
            if column + 1 < size:
                pairs.append(((column, row), (column + 1, row)))
            if row + 1 < size:
                pairs.append(((column, row), (column, row + 1)))
    return pairs


def _swapped(board: Board, first: Cell, second: Cell) -> List[List[int]]:
    grid = [list(column) for column in board]
    (col_a, row_a), (col_b, row_b) = first, second
    grid[col_a][row_a], grid[col_b][row_b] = grid[col_b][row_b], grid[col_a][row_a]
    return grid


def _completes_line(grid: Sequence[Sequence[int]]) -> bool:
    """True if some whole row or whole column holds a single token."""
    size = len(grid)
    if any(len(set(column)) == 1 for column in grid):
        return True
    return any(
        len({grid[column][row] for column in range(size)}) == 1 for row in range(size)
    )


def solve_board(board: Board) -> List[List[int]]:
    """Return ``[[col_a, row_a], [col_b, row_b]]`` — the two cells to swap."""
    size = len(board)
    if size == 0 or any(len(column) != size for column in board):
        raise GeeTestSolveFailed(f"match board is not square: {board!r}")

    for first, second in _neighbours(size):
        if _completes_line(_swapped(board, first, second)):
            return [[first[0], first[1]], [second[0], second[1]]]

    raise GeeTestSolveFailed(
        f"match board has no adjacent swap completing a line: {board!r}"
    )


def answer_fields(board: Board) -> dict:
    """The ``userresponse`` payload fragment for a match challenge."""
    return {"userresponse": solve_board(board)}


__all__ = ["answer_fields", "solve_board"]
