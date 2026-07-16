"""Ball entity for Pong."""

from __future__ import annotations

from dataclasses import dataclass

import pygame


@dataclass
class Ball:
    """Frame-rate-independent Pong ball."""

    x: float
    y: float
    size: int
    velocity_x: float
    velocity_y: float

    @property
    def bounds(self) -> pygame.Rect:
        return pygame.Rect(
            round(self.x),
            round(self.y),
            self.size,
            self.size,
        )

    @property
    def center_x(self) -> float:
        return self.x + self.size / 2.0

    @property
    def center_y(self) -> float:
        return self.y + self.size / 2.0

    def update(self, delta_time: float) -> None:
        self.x += self.velocity_x * delta_time
        self.y += self.velocity_y * delta_time

    def reset(
        self,
        x: float,
        y: float,
        velocity_x: float,
        velocity_y: float,
    ) -> None:
        self.x = x
        self.y = y
        self.velocity_x = velocity_x
        self.velocity_y = velocity_y