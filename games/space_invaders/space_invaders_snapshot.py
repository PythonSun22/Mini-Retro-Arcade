"""Immutable Space Invaders presentation contract."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum, auto

from games.space_invaders.enemy import EnemyKind
from games.space_invaders.projectile import ProjectileOwner


class MatchStatus(Enum):
    WAITING_TO_START = auto()
    ACTIVE = auto()
    COMPLETED = auto()


class MatchOutcome(Enum):
    NONE = auto()
    VICTORY = auto()
    DEFEAT = auto()


class CompletionReason(Enum):
    NONE = auto()
    ALL_WAVES_CLEARED = auto()
    LIVES_DEPLETED = auto()
    INVASION_REACHED_PLAYER = auto()


@dataclass(frozen=True)
class PlayerSnapshot:
    x: float
    y: float
    width: float
    height: float
    lives: int
    invulnerable: bool


@dataclass(frozen=True)
class EnemySnapshot:
    enemy_id: int
    x: float
    y: float
    width: float
    height: float
    kind: EnemyKind


@dataclass(frozen=True)
class ProjectileSnapshot:
    x: float
    y: float
    width: float
    height: float
    owner: ProjectileOwner


@dataclass(frozen=True)
class SpaceInvadersSnapshot:
    """Frozen SpaceInvadersSnapshot v1."""
    version: int
    world_width: int
    world_height: int
    player: PlayerSnapshot
    enemies: tuple[EnemySnapshot, ...]
    projectiles: tuple[ProjectileSnapshot, ...]
    score: int
    wave: int
    waves_completed: int
    enemies_destroyed: int
    match_status: MatchStatus
    outcome: MatchOutcome
    completion_reason: CompletionReason
    show_start_prompt: bool
