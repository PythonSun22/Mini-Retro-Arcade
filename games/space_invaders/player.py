"""Player ship domain entity."""
from __future__ import annotations
from dataclasses import dataclass


@dataclass
class Player:
    x: float
    y: float
    width: float = 44.0
    height: float = 22.0
    speed: float = 300.0
    lives: int = 3

    def move(self, direction: float, delta_time: float, world_width: float) -> None:
        if direction < -1.0 or direction > 1.0:
            raise ValueError("Player direction must be between -1 and 1.")
        self.x += direction * self.speed * delta_time
        self.x = max(0.0, min(self.x, world_width - self.width))

    @property
    def center_x(self) -> float:
        return self.x + self.width / 2.0
