"""Projectile domain entity."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum, auto


class ProjectileOwner(Enum):
    PLAYER = auto()
    ENEMY = auto()


@dataclass
class Projectile:
    x: float
    y: float
    velocity_y: float
    owner: ProjectileOwner
    width: float = 4.0
    height: float = 12.0

    def update(self, delta_time: float) -> None:
        self.y += self.velocity_y * delta_time
