"""Authoritative deterministic Space Invaders simulation."""
from __future__ import annotations

from games.space_invaders.formation import Formation
from games.space_invaders.player import Player
from games.space_invaders.projectile import Projectile, ProjectileOwner
from games.space_invaders.space_invaders_rules import SpaceInvadersRules
from games.space_invaders.space_invaders_snapshot import (
    CompletionReason,
    EnemySnapshot,
    MatchOutcome,
    MatchStatus,
    PlayerSnapshot,
    ProjectileSnapshot,
    SpaceInvadersSnapshot,
)


class SpaceInvadersWorld:
    WORLD_WIDTH = 800
    WORLD_HEIGHT = 600
    SNAPSHOT_VERSION = 1
    PLAYER_Y = 548.0
    FORMATION_ROWS = 4
    FORMATION_COLUMNS = 8

    def __init__(self, *, world_width: int = WORLD_WIDTH, world_height: int = WORLD_HEIGHT) -> None:
        if world_width < 400 or world_height < 400:
            raise ValueError("Space Invaders world is too small.")
        self.world_width = world_width
        self.world_height = world_height
        self.rules = SpaceInvadersRules()
        self.restart()

    def restart(self) -> None:
        self.player = Player(
            x=(self.world_width - 44.0) / 2.0,
            y=min(self.PLAYER_Y, self.world_height - 42.0),
        )
        self.wave = 1
        self.waves_completed = 0
        self.score = 0
        self.enemies_destroyed = 0
        self.match_status = MatchStatus.WAITING_TO_START
        self.outcome = MatchOutcome.NONE
        self.completion_reason = CompletionReason.NONE
        self.projectiles: list[Projectile] = []
        self._move_axis = 0.0
        self._fire_requested = False
        self._fire_cooldown = 0.0
        self._enemy_fire_accumulator = 0.0
        self._enemy_shooter_index = 0
        self._invulnerability_remaining = 0.0
        self.formation = self._create_formation()

    def set_move_axis(self, axis: float) -> None:
        if axis < -1.0 or axis > 1.0:
            raise ValueError("Movement axis must be between -1 and 1.")
        self._move_axis = axis
        if self.match_status is MatchStatus.WAITING_TO_START and axis != 0.0:
            self.match_status = MatchStatus.ACTIVE

    def request_fire(self) -> bool:
        if self.match_status is MatchStatus.COMPLETED:
            return False
        self._fire_requested = True
        if self.match_status is MatchStatus.WAITING_TO_START:
            self.match_status = MatchStatus.ACTIVE
        return True

    def update(self, delta_time: float) -> None:
        if delta_time < 0.0:
            raise ValueError("Delta time cannot be negative.")
        if self.match_status is not MatchStatus.ACTIVE:
            return

        self._fire_cooldown = max(0.0, self._fire_cooldown - delta_time)
        self._invulnerability_remaining = max(0.0, self._invulnerability_remaining - delta_time)
        self.player.move(self._move_axis, delta_time, self.world_width)
        self._consume_player_fire()
        self.formation.advance(delta_time, self.world_width)
        self._spawn_enemy_fire(delta_time)
        for projectile in self.projectiles:
            projectile.update(delta_time)
        self._resolve_collisions()
        self._remove_offscreen_projectiles()
        if self.match_status is MatchStatus.COMPLETED:
            return
        if self.formation.lowest_edge() >= self.player.y:
            self._complete_defeat(CompletionReason.INVASION_REACHED_PLAYER)
            return
        if not self.formation.enemies:
            self._complete_wave()

    def snapshot(self) -> SpaceInvadersSnapshot:
        return SpaceInvadersSnapshot(
            version=self.SNAPSHOT_VERSION,
            world_width=self.world_width,
            world_height=self.world_height,
            player=PlayerSnapshot(
                x=self.player.x,
                y=self.player.y,
                width=self.player.width,
                height=self.player.height,
                lives=self.player.lives,
                invulnerable=self._invulnerability_remaining > 0.0,
            ),
            enemies=tuple(
                EnemySnapshot(
                    enemy_id=enemy.enemy_id,
                    x=enemy.x,
                    y=enemy.y,
                    width=enemy.width,
                    height=enemy.height,
                    kind=enemy.kind,
                )
                for enemy in self.formation.enemies
            ),
            projectiles=tuple(
                ProjectileSnapshot(
                    x=projectile.x,
                    y=projectile.y,
                    width=projectile.width,
                    height=projectile.height,
                    owner=projectile.owner,
                )
                for projectile in self.projectiles
            ),
            score=self.score,
            wave=self.wave,
            waves_completed=self.waves_completed,
            enemies_destroyed=self.enemies_destroyed,
            match_status=self.match_status,
            outcome=self.outcome,
            completion_reason=self.completion_reason,
            show_start_prompt=self.match_status is MatchStatus.WAITING_TO_START,
        )

    def _create_formation(self) -> Formation:
        formation_width = self.FORMATION_COLUMNS * 32.0 + (self.FORMATION_COLUMNS - 1) * 14.0
        return Formation.create(
            rows=self.FORMATION_ROWS,
            columns=self.FORMATION_COLUMNS,
            origin_x=(self.world_width - formation_width) / 2.0,
            origin_y=72.0,
            movement_interval=self.rules.formation_interval_for_wave(self.wave),
        )

    def _consume_player_fire(self) -> None:
        if not self._fire_requested:
            return
        self._fire_requested = False
        active_player_shot = any(p.owner is ProjectileOwner.PLAYER for p in self.projectiles)
        if active_player_shot or self._fire_cooldown > 0.0:
            return
        self.projectiles.append(
            Projectile(
                x=self.player.center_x - 2.0,
                y=self.player.y - 12.0,
                velocity_y=self.rules.PLAYER_PROJECTILE_SPEED,
                owner=ProjectileOwner.PLAYER,
            )
        )
        self._fire_cooldown = self.rules.PLAYER_FIRE_COOLDOWN

    def _spawn_enemy_fire(self, delta_time: float) -> None:
        shooters = self.formation.bottom_shooters()
        if not shooters:
            return
        self._enemy_fire_accumulator += delta_time
        interval = self.rules.enemy_fire_interval_for_wave(self.wave)
        while self._enemy_fire_accumulator >= interval:
            self._enemy_fire_accumulator -= interval
            shooter = shooters[self._enemy_shooter_index % len(shooters)]
            self._enemy_shooter_index += 1
            self.projectiles.append(
                Projectile(
                    x=shooter.x + shooter.width / 2.0 - 2.0,
                    y=shooter.y + shooter.height,
                    velocity_y=self.rules.ENEMY_PROJECTILE_SPEED,
                    owner=ProjectileOwner.ENEMY,
                )
            )

    def _resolve_collisions(self) -> None:
        spent: set[int] = set()
        for index, projectile in enumerate(self.projectiles):
            if projectile.owner is ProjectileOwner.PLAYER:
                hit = next(
                    (enemy for enemy in self.formation.enemies if self.rules.intersects(projectile, enemy)),
                    None,
                )
                if hit is not None:
                    self.formation.remove(hit)
                    self.score += hit.score_value
                    self.enemies_destroyed += 1
                    spent.add(index)
            elif (
                self._invulnerability_remaining <= 0.0
                and self.rules.intersects(projectile, self.player)
            ):
                spent.add(index)
                self.player.lives -= 1
                self._invulnerability_remaining = self.rules.PLAYER_INVULNERABILITY
                if self.player.lives <= 0:
                    self.player.lives = 0
                    self._complete_defeat(CompletionReason.LIVES_DEPLETED)
                    break
        if spent:
            self.projectiles = [p for i, p in enumerate(self.projectiles) if i not in spent]

    def _remove_offscreen_projectiles(self) -> None:
        self.projectiles = [
            projectile for projectile in self.projectiles
            if projectile.y + projectile.height >= 0.0 and projectile.y <= self.world_height
        ]

    def _complete_wave(self) -> None:
        self.waves_completed += 1
        self.score += self.rules.WAVE_CLEAR_BONUS
        self.projectiles.clear()
        if self.wave >= self.rules.MAX_WAVES:
            self.match_status = MatchStatus.COMPLETED
            self.outcome = MatchOutcome.VICTORY
            self.completion_reason = CompletionReason.ALL_WAVES_CLEARED
            return
        self.wave += 1
        self._enemy_fire_accumulator = 0.0
        self.formation = self._create_formation()

    def _complete_defeat(self, reason: CompletionReason) -> None:
        self.match_status = MatchStatus.COMPLETED
        self.outcome = MatchOutcome.DEFEAT
        self.completion_reason = reason
