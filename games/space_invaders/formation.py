"""Deterministic enemy formation model."""
from __future__ import annotations
from dataclasses import dataclass, field

from games.space_invaders.enemy import Enemy, EnemyKind


@dataclass
class Formation:
    enemies: list[Enemy] = field(default_factory=list)
    direction: int = 1
    movement_interval: float = 0.65
    horizontal_step: float = 14.0
    downward_step: float = 18.0
    _accumulator: float = 0.0

    @classmethod
    def create(
        cls,
        *,
        rows: int,
        columns: int,
        origin_x: float,
        origin_y: float,
        horizontal_gap: float = 14.0,
        vertical_gap: float = 12.0,
        movement_interval: float = 0.65,
    ) -> "Formation":
        if rows <= 0 or columns <= 0:
            raise ValueError("Formation rows and columns must be positive.")
        enemies: list[Enemy] = []
        next_id = 0
        for row in range(rows):
            kind = (
                EnemyKind.COMMANDER if row == 0
                else EnemyKind.SOLDIER if row < max(2, rows - 1)
                else EnemyKind.SCOUT
            )
            for column in range(columns):
                enemies.append(
                    Enemy(
                        enemy_id=next_id,
                        row=row,
                        column=column,
                        x=origin_x + column * (32.0 + horizontal_gap),
                        y=origin_y + row * (22.0 + vertical_gap),
                        kind=kind,
                    )
                )
                next_id += 1
        return cls(enemies=enemies, movement_interval=movement_interval)

    def advance(self, delta_time: float, world_width: float) -> int:
        """Advance at fixed intervals and return logical steps performed."""
        if delta_time < 0.0:
            raise ValueError("Delta time cannot be negative.")
        self._accumulator += delta_time
        steps = 0
        while self._accumulator >= self.movement_interval and self.enemies:
            self._accumulator -= self.movement_interval
            self._step_once(world_width)
            steps += 1
        return steps

    def bottom_shooters(self) -> tuple[Enemy, ...]:
        bottom_by_column: dict[int, Enemy] = {}
        for enemy in self.enemies:
            current = bottom_by_column.get(enemy.column)
            if current is None or enemy.row > current.row:
                bottom_by_column[enemy.column] = enemy
        return tuple(bottom_by_column[key] for key in sorted(bottom_by_column))

    def remove(self, enemy: Enemy) -> None:
        self.enemies.remove(enemy)

    def lowest_edge(self) -> float:
        return max((enemy.y + enemy.height for enemy in self.enemies), default=0.0)

    def _step_once(self, world_width: float) -> None:
        dx = self.direction * self.horizontal_step
        would_cross = any(
            enemy.x + dx < 0.0 or enemy.x + enemy.width + dx > world_width
            for enemy in self.enemies
        )
        if would_cross:
            self.direction *= -1
            for enemy in self.enemies:
                enemy.y += self.downward_step
            return
        for enemy in self.enemies:
            enemy.x += dx
