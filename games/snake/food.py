"""Food entity for Snake."""

from __future__ import annotations

from dataclasses import dataclass

from games.snake.grid import GridPosition


@dataclass
class Food:
    """Own only the logical grid position of the current food."""

    position: GridPosition | None
