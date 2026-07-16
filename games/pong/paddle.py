"""Paddle entities for Pong."""

from __future__ import annotations

from dataclasses import dataclass

import pygame


@dataclass
class Paddle:
    """A vertically moving Pong paddle."""

    x: float
    y: float
    width: int
    height: int
    speed: float
    playfield_height: int

    velocity_y: float = 0.0

    @property
    def bounds(self) -> pygame.Rect:
        """Return integer collision bounds."""
        return pygame.Rect(
            round(self.x),
            round(self.y),
            self.width,
            self.height,
        )

    @property
    def center_y(self) -> float:
        return self.y + self.height / 2.0

    def set_direction(self, direction: float) -> None:
        """Set normalized vertical movement direction."""
        clamped_direction = max(-1.0, min(1.0, direction))
        self.velocity_y = clamped_direction * self.speed

    def stop(self) -> None:
        self.velocity_y = 0.0

    def update(self, delta_time: float) -> None:
        """Move the paddle while enforcing playfield limits."""
        self.y += self.velocity_y * delta_time
        self._clamp_to_playfield()

    def reset(self, y: float) -> None:
        self.y = y
        self.velocity_y = 0.0
        self._clamp_to_playfield()

    def _clamp_to_playfield(self) -> None:
        maximum_y = self.playfield_height - self.height
        self.y = max(0.0, min(self.y, float(maximum_y)))


@dataclass
class AIPaddle(Paddle):
    """A limited Pong AI paddle."""

    tracking_dead_zone: float = 18.0

    def react_to_ball(
        self,
        ball_center_y: float,
        delta_time: float,
    ) -> None:
        """Move toward the ball without perfectly matching it."""
        difference = ball_center_y - self.center_y

        if abs(difference) <= self.tracking_dead_zone:
            self.stop()
        elif difference < 0.0:
            self.set_direction(-1.0)
        else:
            self.set_direction(1.0)

        self.update(delta_time)