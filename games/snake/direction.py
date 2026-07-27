"""Cardinal movement directions for Snake."""

from __future__ import annotations

from enum import Enum


class Direction(Enum):
    """A logical one-cell movement direction."""

    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)

    @property
    def vector(self) -> tuple[int, int]:
        """Return the direction as an ``(x, y)`` grid offset."""
        return self.value

    def is_opposite(self, other: "Direction") -> bool:
        """Return whether this direction reverses ``other``."""
        x, y = self.vector
        other_x, other_y = other.vector
        return x + other_x == 0 and y + other_y == 0
