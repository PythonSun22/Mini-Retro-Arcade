"""Backend tests for Pong entities, rules, and world behavior."""

from __future__ import annotations

import random

import pygame
import pytest

from games.pong.ball import Ball
from games.pong.paddle import AIPaddle, Paddle
from games.pong.pong_rules import PongRules
from games.pong.pong_world import PongWorld, RoundStatus


class FixedRandom:
    """Deterministic random source for serve tests."""

    def __init__(self, choices: list[int]) -> None:
        self._choices = iter(choices)

    def choice(self, sequence: tuple[int, ...]) -> int:
        value = next(self._choices)

        if value not in sequence:
            raise ValueError(
                f"Fixed value {value} is not available in {sequence}."
            )

        return value


@pytest.fixture(autouse=True)
def pygame_runtime() -> None:
    pygame.init()
    yield
    pygame.quit()


@pytest.fixture
def rules() -> PongRules:
    return PongRules(
        playfield_width=960,
        playfield_height=540,
        winning_score=5,
        ball_speed_x=390.0,
        ball_speed_y=310.0,
        random_source=FixedRandom([1, -1]),
    )


def test_player_paddle_stops_at_top_boundary() -> None:
    paddle = Paddle(
        x=42.0,
        y=10.0,
        width=18,
        height=110,
        speed=430.0,
        playfield_height=540,
    )

    paddle.set_direction(-1.0)
    paddle.update(1.0)

    assert paddle.y == 0.0


def test_player_paddle_stops_at_bottom_boundary() -> None:
    paddle = Paddle(
        x=42.0,
        y=400.0,
        width=18,
        height=110,
        speed=430.0,
        playfield_height=540,
    )

    paddle.set_direction(1.0)
    paddle.update(1.0)

    assert paddle.y == 430.0


def test_ball_movement_uses_delta_time() -> None:
    ball = Ball(
        x=100.0,
        y=100.0,
        size=18,
        velocity_x=400.0,
        velocity_y=-200.0,
    )

    ball.update(0.25)

    assert ball.x == pytest.approx(200.0)
    assert ball.y == pytest.approx(50.0)


def test_top_wall_collision_reflects_ball(
    rules: PongRules,
) -> None:
    ball = Ball(
        x=400.0,
        y=-5.0,
        size=18,
        velocity_x=390.0,
        velocity_y=-310.0,
    )

    rules.resolve_wall_collision(ball)

    assert ball.y == 0.0
    assert ball.velocity_y == 310.0


def test_bottom_wall_collision_reflects_ball(
    rules: PongRules,
) -> None:
    ball = Ball(
        x=400.0,
        y=530.0,
        size=18,
        velocity_x=390.0,
        velocity_y=310.0,
    )

    rules.resolve_wall_collision(ball)

    assert ball.y == 522.0
    assert ball.velocity_y == -310.0


def test_left_paddle_collision_sends_ball_right(
    rules: PongRules,
) -> None:
    paddle = Paddle(
        x=42.0,
        y=200.0,
        width=18,
        height=110,
        speed=430.0,
        playfield_height=540,
    )

    ball = Ball(
        x=50.0,
        y=240.0,
        size=18,
        velocity_x=-390.0,
        velocity_y=0.0,
    )

    collision_occurred = rules.resolve_paddle_collision(
        ball,
        paddle,
        horizontal_direction=1,
    )

    assert collision_occurred is True
    assert ball.velocity_x == 390.0
    assert ball.x == float(paddle.bounds.right)


def test_right_paddle_collision_sends_ball_left(
    rules: PongRules,
) -> None:
    paddle = Paddle(
        x=900.0,
        y=200.0,
        width=18,
        height=110,
        speed=335.0,
        playfield_height=540,
    )

    ball = Ball(
        x=895.0,
        y=240.0,
        size=18,
        velocity_x=390.0,
        velocity_y=0.0,
    )

    collision_occurred = rules.resolve_paddle_collision(
        ball,
        paddle,
        horizontal_direction=-1,
    )

    assert collision_occurred is True
    assert ball.velocity_x == -390.0
    assert ball.x == float(paddle.bounds.left - ball.size)


def test_paddle_impact_changes_vertical_velocity(
    rules: PongRules,
) -> None:
    paddle = Paddle(
        x=42.0,
        y=200.0,
        width=18,
        height=110,
        speed=430.0,
        playfield_height=540,
    )

    ball = Ball(
        x=50.0,
        y=200.0,
        size=18,
        velocity_x=-390.0,
        velocity_y=0.0,
    )

    rules.resolve_paddle_collision(
        ball,
        paddle,
        horizontal_direction=1,
    )

    assert ball.velocity_y < 0.0
    assert abs(ball.velocity_y) <= rules.ball_speed_y


def test_ai_respects_maximum_movement_speed() -> None:
    paddle = AIPaddle(
        x=900.0,
        y=200.0,
        width=18,
        height=110,
        speed=300.0,
        playfield_height=540,
        tracking_dead_zone=20.0,
    )

    paddle.react_to_ball(
        ball_center_y=500.0,
        delta_time=0.5,
    )

    assert paddle.velocity_y == 300.0
    assert 200.0 < paddle.y < 350.0


def test_ai_tracks_old_target_until_reaction_interval_elapses() -> None:
    paddle = PongWorld().ai_paddle
    paddle.react_to_ball(500.0, 0.0)
    initial_y = paddle.y

    # A sudden direction change should not cause an immediate CPU reaction.
    paddle.react_to_ball(0.0, 0.09)
    assert initial_y < paddle.y < initial_y + paddle.speed * 0.09
    paddle.react_to_ball(0.0, 0.08)
    previous_velocity = paddle.velocity_y
    assert previous_velocity > 0.0

    paddle.react_to_ball(0.0, 0.011)
    assert 0.0 < paddle.velocity_y < previous_velocity


def test_ai_reset_discards_previous_target_and_reaction_timer() -> None:
    paddle = PongWorld().ai_paddle
    paddle.react_to_ball(500.0, 0.0)
    paddle.react_to_ball(500.0, 0.17)
    paddle.reset(200.0)

    assert paddle.velocity_y == 0.0
    paddle.react_to_ball(0.0, 0.01)
    assert paddle.velocity_y < 0.0
    paddle.react_to_ball(500.0, 0.02)
    assert paddle.velocity_y < 0.0


def test_ai_accelerates_and_reverses_gradually() -> None:
    paddle = PongWorld().ai_paddle
    paddle.react_to_ball(500.0, 0.0)
    for _ in range(24):
        previous_velocity = paddle.velocity_y
        paddle.react_to_ball(500.0, 1.0 / 120.0)
        assert abs(paddle.velocity_y - previous_velocity) <= 1800.0 / 120.0 + 1e-8
        assert abs(paddle.velocity_y) <= 285.0
    assert paddle.velocity_y == pytest.approx(285.0)

    for _ in range(60):
        previous_velocity = paddle.velocity_y
        paddle.react_to_ball(0.0, 1.0 / 120.0)
        assert abs(paddle.velocity_y - previous_velocity) <= 1800.0 / 120.0 + 1e-8
    assert paddle.velocity_y < 0.0


@pytest.mark.parametrize('fps', [30, 60, 144])
def test_ai_settles_at_target_without_oscillation(fps: int) -> None:
    paddle = PongWorld().ai_paddle
    target = 400.0
    positions = []
    for _ in range(fps * 3):
        paddle.react_to_ball(target, 1.0 / fps)
        positions.append(paddle.center_y)
    assert abs(target - paddle.center_y) <= paddle.tracking_dead_zone + 0.1
    assert abs(paddle.velocity_y) < 0.1
    assert all(a <= b + 1e-8 for a, b in zip(positions, positions[1:]))


def test_ai_stops_inside_tracking_dead_zone() -> None:
    paddle = AIPaddle(
        x=900.0,
        y=200.0,
        width=18,
        height=110,
        speed=300.0,
        playfield_height=540,
        tracking_dead_zone=20.0,
    )

    paddle.react_to_ball(
        ball_center_y=paddle.center_y + 10.0,
        delta_time=0.5,
    )

    assert paddle.velocity_y == 0.0
    assert paddle.y == 200.0


def test_player_scores_when_ball_leaves_right_side(
    rules: PongRules,
) -> None:
    ball = Ball(
        x=961.0,
        y=200.0,
        size=18,
        velocity_x=390.0,
        velocity_y=0.0,
    )

    result = rules.detect_score(ball)

    assert result.goal_occurred is True
    assert result.player_scored is True
    assert result.ai_scored is False


def test_ai_scores_when_ball_leaves_left_side(
    rules: PongRules,
) -> None:
    ball = Ball(
        x=-20.0,
        y=200.0,
        size=18,
        velocity_x=-390.0,
        velocity_y=0.0,
    )

    result = rules.detect_score(ball)

    assert result.goal_occurred is True
    assert result.ai_scored is True
    assert result.player_scored is False


def test_serve_velocity_can_be_deterministic() -> None:
    rules = PongRules(
        playfield_width=960,
        playfield_height=540,
        winning_score=5,
        ball_speed_x=390.0,
        ball_speed_y=310.0,
        random_source=FixedRandom([-1]),
    )

    velocity_x, velocity_y = rules.create_serve_velocity(
        horizontal_direction=1,
    )

    assert velocity_x == 390.0
    assert velocity_y == -155.0


def test_world_starts_waiting_for_serve() -> None:
    world = PongWorld(random_source=random.Random(1))

    snapshot = world.snapshot()

    assert snapshot.player_score == 0
    assert snapshot.ai_score == 0
    assert snapshot.round_status is RoundStatus.WAITING_TO_SERVE
    assert snapshot.show_serve_prompt is True
    assert world.ball.velocity_x == 0.0
    assert world.ball.velocity_y == 0.0


def test_start_serve_activates_round() -> None:
    world = PongWorld(random_source=random.Random(1))

    serve_started = world.start_serve()

    assert serve_started is True
    assert world.round_status is RoundStatus.ACTIVE
    assert world.ball.velocity_x != 0.0


def test_start_serve_is_rejected_during_active_round() -> None:
    world = PongWorld(random_source=random.Random(1))

    assert world.start_serve() is True
    assert world.start_serve() is False


def test_scoring_increments_exactly_once_and_resets_round() -> None:
    world = PongWorld(random_source=random.Random(1))
    world.start_serve()

    world.ball.x = float(world.WIDTH + 1)
    world.ball.velocity_x = world.BALL_SPEED_X

    world.update(0.0)

    assert world.player_score == 1
    assert world.ai_score == 0
    assert world.round_status is RoundStatus.WAITING_TO_SERVE
    assert world.ball.velocity_x == 0.0
    assert world.ball.velocity_y == 0.0

    world.update(0.0)

    assert world.player_score == 1


def test_round_reset_centers_ball() -> None:
    world = PongWorld(random_source=random.Random(1))
    world.start_serve()

    world.ball.x = float(world.WIDTH + 1)
    world.update(0.0)

    expected_x = (world.WIDTH - world.BALL_SIZE) / 2.0
    expected_y = (world.HEIGHT - world.BALL_SIZE) / 2.0

    assert world.ball.x == expected_x
    assert world.ball.y == expected_y


def test_winning_score_completes_match() -> None:
    world = PongWorld(
        winning_score=1,
        random_source=random.Random(1),
    )
    world.start_serve()

    world.ball.x = float(world.WIDTH + 1)
    world.update(0.0)

    assert world.player_score == 1
    assert world.round_status is RoundStatus.MATCH_COMPLETE
    assert world.match_result == "player"
    assert world.ball.velocity_x == 0.0
    assert world.ball.velocity_y == 0.0


def test_restart_match_creates_fresh_match_state() -> None:
    world = PongWorld(
        winning_score=1,
        random_source=random.Random(1),
    )

    world.start_serve()
    world.ball.x = float(world.WIDTH + 1)
    world.update(0.0)

    world.restart_match()

    assert world.player_score == 0
    assert world.ai_score == 0
    assert world.match_result is None
    assert world.round_status is RoundStatus.WAITING_TO_SERVE
    assert world.player_paddle.velocity_y == 0.0
    assert world.ai_paddle.velocity_y == 0.0
