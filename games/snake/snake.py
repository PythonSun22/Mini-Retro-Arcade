"""Snake entity for the logical grid simulation."""

from __future__ import annotations

from dataclasses import dataclass, field

from games.snake.direction import Direction
from games.snake.grid import GridPosition


@dataclass
class Snake:
    """Ordered Snake body with the head stored at index zero."""

    body: list[GridPosition] = field(default_factory=list)
    direction: Direction = Direction.RIGHT

    def __post_init__(self) -> None:
        self._validate_body(self.body)

    @property
    def head(self) -> GridPosition:
        return self.body[0]

    @property
    def tail(self) -> GridPosition:
        return self.body[-1]

    def advance(self, new_head: GridPosition, *, grow: bool = False) -> None:
        """Advance one cell, preserving the tail when growth is requested."""
        self.body.insert(0, new_head)
        if not grow:
            self.body.pop()

    def move_to(self, new_head: GridPosition) -> None:
        """Backward-compatible non-growing movement helper."""
        self.advance(new_head)

    def reset(
        self,
        body: tuple[GridPosition, ...],
        direction: Direction,
    ) -> None:
        """Restore a fresh body and direction."""
        self._validate_body(body)
        self.body = list(body)
        self.direction = direction

    @staticmethod
    def _validate_body(body: list[GridPosition] | tuple[GridPosition, ...]) -> None:
        if not body:
            raise ValueError("Snake body cannot be empty.")
        if len(set(body)) != len(body):
            raise ValueError("Snake body positions must be unique.")
