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
        if not self.body:
            raise ValueError("Snake body cannot be empty.")

        if len(set(self.body)) != len(self.body):
            raise ValueError("Snake body positions must be unique.")

    @property
    def head(self) -> GridPosition:
        return self.body[0]

    def move_to(self, new_head: GridPosition) -> None:
        """Advance one cell without growth."""
        self.body.insert(0, new_head)
        self.body.pop()

    def reset(
        self,
        body: tuple[GridPosition, ...],
        direction: Direction,
    ) -> None:
        """Restore a fresh body and direction."""
        if not body:
            raise ValueError("Snake body cannot be empty.")

        if len(set(body)) != len(body):
            raise ValueError("Snake body positions must be unique.")

        self.body = list(body)
        self.direction = direction
