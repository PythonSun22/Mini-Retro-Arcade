"""Paddle entities for Pong."""

from __future__ import annotations

from dataclasses import dataclass, field

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
    tracking_interval: float = 0.180
    acceleration: float = 1800.0
    arrival_time: float = 0.12
    _target_y: float | None = field(default=None, init=False, repr=False)
    _tracking_elapsed: float = field(default=0.0, init=False, repr=False)

    def reset(self, y: float) -> None:
        super().reset(y)
        self._target_y = None
        self._tracking_elapsed = 0.0

    def react_to_ball(
        self,
        ball_center_y: float,
        delta_time: float,
    ) -> None:
        """Sample the ball periodically, but move toward that target every frame."""
        if self._target_y is None:
            self._target_y = ball_center_y
        else:
            self._tracking_elapsed += delta_time
            if self._tracking_elapsed >= self.tracking_interval:
                self._target_y = ball_center_y
                self._tracking_elapsed %= self.tracking_interval

        # Small integration steps keep braking stable even on a slow frame.
        remaining = delta_time
        while remaining > 0.0:
            step = min(remaining, 1.0 / 120.0)
            difference = self._target_y - self.center_y
            distance = max(0.0, abs(difference) - self.tracking_dead_zone)
            desired_speed = min(self.speed, distance / self.arrival_time)
            desired_velocity = desired_speed if difference > 0.0 else -desired_speed
            velocity_change = desired_velocity - self.velocity_y
            limit = self.acceleration * step
            self.velocity_y += max(-limit, min(limit, velocity_change))
            self.update(step)
            if (self.y <= 0.0 and self.velocity_y < 0.0) or (
                self.y >= self.playfield_height - self.height and self.velocity_y > 0.0
            ):
                self.stop()
            remaining -= step
