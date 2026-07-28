"""Pure Space Invaders gameplay rules."""
from __future__ import annotations
from typing import Protocol


class RectLike(Protocol):
    x: float
    y: float
    width: float
    height: float


class SpaceInvadersRules:
    PLAYER_PROJECTILE_SPEED = -430.0
    ENEMY_PROJECTILE_SPEED = 245.0
    PLAYER_FIRE_COOLDOWN = 0.22
    PLAYER_INVULNERABILITY = 1.0
    MAX_WAVES = 3
    WAVE_CLEAR_BONUS = 250

    @staticmethod
    def intersects(first: RectLike, second: RectLike) -> bool:
        return (
            first.x < second.x + second.width
            and first.x + first.width > second.x
            and first.y < second.y + second.height
            and first.y + first.height > second.y
        )

    @staticmethod
    def formation_interval_for_wave(wave: int) -> float:
        if wave <= 0:
            raise ValueError("Wave must be positive.")
        return max(0.20, 0.65 - (wave - 1) * 0.10)

    @staticmethod
    def enemy_fire_interval_for_wave(wave: int) -> float:
        if wave <= 0:
            raise ValueError("Wave must be positive.")
        return max(0.45, 1.25 - (wave - 1) * 0.18)
