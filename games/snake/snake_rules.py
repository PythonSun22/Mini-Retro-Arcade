"""Authoritative, presentation-independent rules for Snake."""

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
    """Centralized movement, collision, scoring, speed, and spawn rules."""

    SCORE_PER_FOOD = 10
    FOODS_PER_SPEED_LEVEL = 5
    SPEED_INTERVAL_DECREMENT = 0.02
    MINIMUM_MOVEMENT_INTERVAL = 0.08

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

    def is_wall_collision(self, position: GridPosition) -> bool:
        return not self.grid.contains(position)

    @staticmethod
    def is_food_collected(
        head: GridPosition,
        food_position: GridPosition | None,
    ) -> bool:
        return food_position is not None and head == food_position

    @staticmethod
    def is_self_collision(
        new_head: GridPosition,
        body: Sequence[GridPosition],
        *,
        growing: bool,
    ) -> bool:
        """Detect body contact while allowing a non-growing tail vacancy."""
        occupied = body if growing else body[:-1]
        return new_head in occupied

    @classmethod
    def score_for_food_count(cls, food_count: int) -> int:
        if food_count < 0:
            raise ValueError("Food count cannot be negative.")
        return food_count * cls.SCORE_PER_FOOD

    @classmethod
    def speed_level_for_food_count(cls, food_count: int) -> int:
        if food_count < 0:
            raise ValueError("Food count cannot be negative.")
        return 1 + food_count // cls.FOODS_PER_SPEED_LEVEL

    @classmethod
    def movement_interval_for_level(
        cls,
        base_interval: float,
        speed_level: int,
    ) -> float:
        if base_interval <= 0.0:
            raise ValueError("Base interval must be greater than zero.")
        if speed_level < 1:
            raise ValueError("Speed level must be at least one.")
        reduced = base_interval - (
            speed_level - 1
        ) * cls.SPEED_INTERVAL_DECREMENT
        return max(cls.MINIMUM_MOVEMENT_INTERVAL, reduced)

    def choose_food_position(
        self,
        occupied: Sequence[GridPosition],
    ) -> GridPosition | None:
        """Choose an unoccupied cell without retry loops."""
        occupied_positions = set(occupied)
        candidates = tuple(
            position
            for position in self.grid.positions()
            if position not in occupied_positions
        )
        if not candidates:
            return None
        return self.random_source.choice(candidates)
