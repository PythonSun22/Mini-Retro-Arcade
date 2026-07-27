"""Configurable logical playfield for Snake."""

from __future__ import annotations

from dataclasses import dataclass


GridPosition = tuple[int, int]


@dataclass(frozen=True)
class Grid:
    """Defines Snake's logical dimensions without presentation details."""

    width: int = 24
    height: int = 18

    def __post_init__(self) -> None:
        if self.width <= 0 or self.height <= 0:
            raise ValueError("Grid dimensions must be greater than zero.")

    def contains(self, position: GridPosition) -> bool:
        """Return whether a logical position lies inside the grid."""
        x, y = position
        return 0 <= x < self.width and 0 <= y < self.height

    def positions(self) -> tuple[GridPosition, ...]:
        """Return every logical position in deterministic row-major order."""
        return tuple(
            (x, y)
            for y in range(self.height)
            for x in range(self.width)
        )
