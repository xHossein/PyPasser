"""Asynchronous GeeTest V4 solver."""

from __future__ import annotations

import asyncio
from typing import Any

from pypasser.captcha.geetest.v4.solver import GeeTestV4Solver


class AsyncGeeTestV4Solver(GeeTestV4Solver):
    """GeeTest V4 solver whose ``solve`` can be awaited."""

    async def solve(
        self, attempts: int = 3
    ) -> dict[str, Any]:
        """Solve a challenge and return the server's ``seccode`` object."""
        return await asyncio.to_thread(GeeTestV4Solver.solve, self, attempts)


__all__ = ["AsyncGeeTestV4Solver"]
