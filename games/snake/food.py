"""Food entity for Snake."""

from __future__ import annotations

from dataclasses import dataclass

from games.snake.grid import GridPosition


@dataclass
class Food:
    """Stores the current logical food position."""

    position: GridPosition
