from dataclasses import FrozenInstanceError

import pytest

from games.space_invaders.enemy import EnemyKind
from games.space_invaders.formation import Formation
from games.space_invaders.projectile import Projectile, ProjectileOwner
from games.space_invaders.space_invaders_result import SpaceInvadersResult
from games.space_invaders.space_invaders_rules import SpaceInvadersRules
from games.space_invaders.space_invaders_snapshot import (
    CompletionReason,
    MatchOutcome,
    MatchStatus,
)
from games.space_invaders.space_invaders_world import SpaceInvadersWorld


def active_world() -> SpaceInvadersWorld:
    world = SpaceInvadersWorld()
    world.set_move_axis(1.0)
    return world


def test_initial_world_waits_with_complete_formation():
    world = SpaceInvadersWorld()
    assert world.match_status is MatchStatus.WAITING_TO_START
    assert len(world.formation.enemies) == 32
    assert world.player.lives == 3
    assert world.snapshot().show_start_prompt


def test_player_movement_is_clamped_to_world():
    world = active_world()
    world.update(100.0)
    assert world.player.x == pytest.approx(world.world_width - world.player.width)
    world.set_move_axis(-1.0)
    world.update(100.0)
    assert world.player.x == 0.0


def test_player_fire_starts_game_and_limits_active_shot():
    world = SpaceInvadersWorld()
    assert world.request_fire()
    world.update(0.0)
    assert world.match_status is MatchStatus.ACTIVE
    assert len([p for p in world.projectiles if p.owner is ProjectileOwner.PLAYER]) == 1
    world.request_fire()
    world.update(0.0)
    assert len([p for p in world.projectiles if p.owner is ProjectileOwner.PLAYER]) == 1


def test_formation_reverses_and_descends_at_edge():
    formation = Formation.create(rows=1, columns=1, origin_x=760.0, origin_y=50.0)
    enemy = formation.enemies[0]
    old_y = enemy.y
    formation.advance(formation.movement_interval, 800.0)
    assert formation.direction == -1
    assert enemy.y == old_y + formation.downward_step
    assert enemy.x == 760.0


def test_formation_moves_horizontally_away_from_edge():
    formation = Formation.create(rows=1, columns=1, origin_x=100.0, origin_y=50.0)
    formation.advance(formation.movement_interval, 800.0)
    assert formation.enemies[0].x == 100.0 + formation.horizontal_step


def test_bottom_shooters_select_lowest_enemy_per_column():
    formation = Formation.create(rows=3, columns=2, origin_x=100.0, origin_y=50.0)
    shooters = formation.bottom_shooters()
    assert len(shooters) == 2
    assert all(enemy.row == 2 for enemy in shooters)


def test_player_projectile_destroys_enemy_and_scores():
    world = active_world()
    target = world.formation.enemies[0]
    expected_score = target.score_value
    world.projectiles = [
        Projectile(
            x=target.x,
            y=target.y,
            velocity_y=0.0,
            owner=ProjectileOwner.PLAYER,
        )
    ]
    world.update(0.0)
    assert target not in world.formation.enemies
    assert world.enemies_destroyed == 1
    assert world.score == expected_score
    assert world.projectiles == []


def test_enemy_projectile_removes_life_and_grants_invulnerability():
    world = active_world()
    world.projectiles = [
        Projectile(
            x=world.player.x,
            y=world.player.y,
            velocity_y=0.0,
            owner=ProjectileOwner.ENEMY,
        ),
        Projectile(
            x=world.player.x + 5.0,
            y=world.player.y,
            velocity_y=0.0,
            owner=ProjectileOwner.ENEMY,
        ),
    ]
    world.update(0.0)
    assert world.player.lives == 2
    assert world.snapshot().player.invulnerable


def test_lives_depleted_completes_defeat():
    world = active_world()
    world.player.lives = 1
    world.projectiles = [
        Projectile(
            x=world.player.x,
            y=world.player.y,
            velocity_y=0.0,
            owner=ProjectileOwner.ENEMY,
        )
    ]
    world.update(0.0)
    assert world.match_status is MatchStatus.COMPLETED
    assert world.outcome is MatchOutcome.DEFEAT
    assert world.completion_reason is CompletionReason.LIVES_DEPLETED
    assert world.player.lives == 0


def test_formation_reaching_player_completes_defeat():
    world = active_world()
    for enemy in world.formation.enemies:
        enemy.y = world.player.y
    world.update(0.0)
    assert world.match_status is MatchStatus.COMPLETED
    assert world.completion_reason is CompletionReason.INVASION_REACHED_PLAYER


def test_wave_clear_awards_bonus_and_creates_next_wave():
    world = active_world()
    world.formation.enemies.clear()
    world.update(0.0)
    assert world.waves_completed == 1
    assert world.wave == 2
    assert world.score == SpaceInvadersRules.WAVE_CLEAR_BONUS
    assert len(world.formation.enemies) == 32
    assert world.match_status is MatchStatus.ACTIVE


def test_final_wave_clear_completes_victory():
    world = active_world()
    world.wave = SpaceInvadersRules.MAX_WAVES
    world.waves_completed = SpaceInvadersRules.MAX_WAVES - 1
    world.formation.enemies.clear()
    world.update(0.0)
    assert world.waves_completed == SpaceInvadersRules.MAX_WAVES
    assert world.match_status is MatchStatus.COMPLETED
    assert world.outcome is MatchOutcome.VICTORY
    assert world.completion_reason is CompletionReason.ALL_WAVES_CLEARED


def test_wave_difficulty_intervals_increase_deterministically():
    assert SpaceInvadersRules.formation_interval_for_wave(2) < SpaceInvadersRules.formation_interval_for_wave(1)
    assert SpaceInvadersRules.enemy_fire_interval_for_wave(2) < SpaceInvadersRules.enemy_fire_interval_for_wave(1)


def test_snapshot_v1_is_deeply_presentation_only_and_immutable():
    snapshot = SpaceInvadersWorld().snapshot()
    assert snapshot.version == 1
    assert snapshot.enemies[0].kind is EnemyKind.COMMANDER
    with pytest.raises(FrozenInstanceError):
        snapshot.score = 10
    with pytest.raises(FrozenInstanceError):
        snapshot.player.lives = 99


def test_result_validates_completion_semantics():
    result = SpaceInvadersResult.create(
        score=1000,
        waves_completed=3,
        enemies_destroyed=96,
        remaining_lives=2,
        outcome=MatchOutcome.VICTORY,
        completion_reason=CompletionReason.ALL_WAVES_CLEARED,
    )
    assert result.outcome is MatchOutcome.VICTORY
    with pytest.raises(ValueError):
        SpaceInvadersResult.create(
            score=0,
            waves_completed=0,
            enemies_destroyed=0,
            remaining_lives=0,
            outcome=MatchOutcome.VICTORY,
            completion_reason=CompletionReason.LIVES_DEPLETED,
        )


def test_restart_restores_fresh_run():
    world = active_world()
    world.score = 500
    world.player.lives = 1
    world.wave = 3
    world.restart()
    assert world.score == 0
    assert world.player.lives == 3
    assert world.wave == 1
    assert world.match_status is MatchStatus.WAITING_TO_START


def test_negative_delta_and_invalid_axis_are_rejected():
    world = SpaceInvadersWorld()
    with pytest.raises(ValueError):
        world.update(-0.01)
    with pytest.raises(ValueError):
        world.set_move_axis(2.0)
