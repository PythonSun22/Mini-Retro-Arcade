"""Minimal authoritative rules for the Snake vertical slice."""

from __future__ import annotations

import random
from typing import Protocol, Sequence, TypeVar

from games.snake.direction import Direction
from games.snake.grid import Grid, GridPosition


T = TypeVar("T")


class RandomSource(Protocol):
    """Minimal random interface required for food placement."""

    def choice(self, sequence: Sequence[T]) -> T:
        ...


class SnakeRules:
    """Direction, movement, and initial food-placement rules."""

    def __init__(
        self,
        grid: Grid,
        random_source: RandomSource | None = None,
    ) -> None:
        self.grid = grid
        self.random_source = random_source or random.Random()

    @staticmethod
    def is_valid_direction_change(
        current: Direction,
        requested: Direction,
    ) -> bool:
        """Reject an immediate 180-degree reversal."""
        return not requested.is_opposite(current)

    @staticmethod
    def next_head(
        head: GridPosition,
        direction: Direction,
    ) -> GridPosition:
        """Return the next logical head position."""
        delta_x, delta_y = direction.vector
        return head[0] + delta_x, head[1] + delta_y

    def choose_food_position(
        self,
        occupied: tuple[GridPosition, ...],
    ) -> GridPosition | None:
        """Choose an unoccupied cell without retry loops.

        ``None`` is reserved for the later full-grid victory behavior.
        """
        occupied_positions = set(occupied)
        candidates = tuple(
            position
            for position in self.grid.positions()
            if position not in occupied_positions
        )

        if not candidates:
            return None

        return self.random_source.choice(candidates)
