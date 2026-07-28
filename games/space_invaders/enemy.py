"""Enemy domain entity."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum, auto


class EnemyKind(Enum):
    SCOUT = auto()
    SOLDIER = auto()
    COMMANDER = auto()


@dataclass
class Enemy:
    enemy_id: int
    row: int
    column: int
    x: float
    y: float
    kind: EnemyKind
    width: float = 32.0
    height: float = 22.0

    @property
    def score_value(self) -> int:
        return {
            EnemyKind.SCOUT: 10,
            EnemyKind.SOLDIER: 20,
            EnemyKind.COMMANDER: 30,
        }[self.kind]
