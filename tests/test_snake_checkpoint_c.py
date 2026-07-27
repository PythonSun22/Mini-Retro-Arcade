from dataclasses import FrozenInstanceError

import pytest

from games.snake.direction import Direction
from games.snake.grid import Grid
from games.snake.snake import Snake
from games.snake.snake_rules import SnakeRules
from games.snake.snake_world import (
    GameOverReason,
    MatchResult,
    MatchStatus,
    SnakeWorld,
)


class FirstChoice:
    def choice(self, sequence):
        return sequence[0]


def active_world(*, grid=Grid(8, 6), interval=0.2):
    world = SnakeWorld(grid=grid, movement_interval=interval, random_source=FirstChoice())
    world.request_direction(Direction.RIGHT)
    return world


def test_snake_advance_without_growth_removes_tail():
    snake = Snake([(2, 1), (1, 1), (0, 1)])
    snake.advance((3, 1))
    assert snake.body == [(3, 1), (2, 1), (1, 1)]


def test_snake_advance_with_growth_preserves_tail():
    snake = Snake([(2, 1), (1, 1), (0, 1)])
    snake.advance((3, 1), grow=True)
    assert snake.body == [(3, 1), (2, 1), (1, 1), (0, 1)]


def test_food_collection_grows_and_scores():
    world = active_world()
    next_head = world.rules.next_head(world.snake.head, world.snake.direction)
    old_length = len(world.snake.body)
    world.food.position = next_head
    world.update(world.movement_interval)
    assert len(world.snake.body) == old_length + 1
    assert world.food_count == 1
    assert world.score == SnakeRules.SCORE_PER_FOOD
    assert world.match_status is MatchStatus.ACTIVE
    assert world.food.position not in world.snake.body


def test_non_food_movement_does_not_grow_or_score():
    world = active_world()
    world.food.position = (0, 0)
    old_length = len(world.snake.body)
    world.update(world.movement_interval)
    assert len(world.snake.body) == old_length
    assert world.score == 0
    assert world.food_count == 0


def test_wall_collision_completes_loss_without_moving_outside_grid():
    world = active_world(grid=Grid(5, 4))
    world.snake.reset(((4, 2), (3, 2), (2, 2)), Direction.RIGHT)
    original_body = tuple(world.snake.body)
    world.update(world.movement_interval)
    assert tuple(world.snake.body) == original_body
    assert world.match_status is MatchStatus.COMPLETED
    assert world.match_result is MatchResult.LOSS
    assert world.game_over_reason is GameOverReason.WALL_COLLISION


def test_self_collision_completes_loss():
    world = active_world()
    world.snake.reset(((2, 2), (2, 3), (1, 3), (1, 2), (1, 1)), Direction.LEFT)
    world.update(world.movement_interval)
    assert world.match_status is MatchStatus.COMPLETED
    assert world.match_result is MatchResult.LOSS
    assert world.game_over_reason is GameOverReason.SELF_COLLISION


def test_moving_into_vacating_tail_cell_is_legal():
    world = active_world()
    world.snake.reset(((2, 2), (2, 3), (1, 3), (1, 2)), Direction.LEFT)
    world.food.position = (7, 5)
    world.update(world.movement_interval)
    assert world.match_status is MatchStatus.ACTIVE
    assert world.snake.head == (1, 2)
    assert world.snake.body == [(1, 2), (2, 2), (2, 3), (1, 3)]


def test_moving_into_tail_while_eating_is_self_collision():
    world = active_world()
    world.snake.reset(((2, 2), (2, 3), (1, 3), (1, 2)), Direction.LEFT)
    world.food.position = (1, 2)
    world.update(world.movement_interval)
    assert world.match_status is MatchStatus.COMPLETED
    assert world.game_over_reason is GameOverReason.SELF_COLLISION


def test_speed_progression_occurs_at_configured_food_threshold():
    world = active_world(grid=Grid(20, 4), interval=0.18)
    for _ in range(SnakeRules.FOODS_PER_SPEED_LEVEL):
        world.food.position = world.rules.next_head(world.snake.head, world.snake.direction)
        world.update(world.movement_interval)
    assert world.food_count == SnakeRules.FOODS_PER_SPEED_LEVEL
    assert world.speed_level == 2
    assert world.movement_interval == pytest.approx(0.16)


def test_speed_interval_is_clamped_to_minimum():
    interval = SnakeRules.movement_interval_for_level(0.18, 999)
    assert interval == SnakeRules.MINIMUM_MOVEMENT_INTERVAL


def test_grid_completion_produces_win_and_no_food():
    world = active_world(grid=Grid(4, 1))
    world.food.position = (3, 0)
    world.update(world.movement_interval)
    assert len(world.snake.body) == 4
    assert world.food.position is None
    assert world.match_status is MatchStatus.COMPLETED
    assert world.match_result is MatchResult.WIN
    assert world.game_over_reason is GameOverReason.GRID_COMPLETED


def test_completed_world_rejects_input_and_stops_updating():
    world = active_world(grid=Grid(5, 4))
    world.snake.reset(((4, 2), (3, 2), (2, 2)), Direction.RIGHT)
    world.update(world.movement_interval)
    body = tuple(world.snake.body)
    assert not world.request_direction(Direction.UP)
    world.update(10.0)
    assert tuple(world.snake.body) == body


def test_restart_resets_progress_speed_and_completion_state():
    world = active_world()
    world.score = 50
    world.food_count = 5
    world.speed_level = 2
    world.movement_interval = 0.16
    world.match_status = MatchStatus.COMPLETED
    world.match_result = MatchResult.LOSS
    world.game_over_reason = GameOverReason.WALL_COLLISION
    world.restart()
    assert world.score == 0
    assert world.food_count == 0
    assert world.speed_level == 1
    assert world.movement_interval == pytest.approx(0.2)
    assert world.match_status is MatchStatus.WAITING_TO_START
    assert world.match_result is MatchResult.NONE
    assert world.game_over_reason is GameOverReason.NONE


def test_snapshot_v1_shape_and_immutability_remain_unchanged():
    world = SnakeWorld(random_source=FirstChoice())
    snapshot = world.snapshot()
    assert snapshot.version == 1
    assert snapshot.snake_head == snapshot.snake_body[0]
    assert snapshot.show_start_prompt
    with pytest.raises(FrozenInstanceError):
        snapshot.score = 1


def test_negative_delta_is_rejected():
    world = SnakeWorld(random_source=FirstChoice())
    with pytest.raises(ValueError):
        world.update(-0.001)


def test_one_buffered_direction_per_step_remains_enforced():
    world = SnakeWorld(random_source=FirstChoice())
    assert world.request_direction(Direction.UP)
    assert not world.request_direction(Direction.LEFT)
    world.update(world.movement_interval)
    assert world.snake.direction is Direction.UP


def test_food_spawn_never_uses_occupied_cell():
    rules = SnakeRules(Grid(4, 1), random_source=FirstChoice())
    assert rules.choose_food_position(((0, 0), (1, 0), (2, 0))) == (3, 0)
    assert rules.choose_food_position(((0, 0), (1, 0), (2, 0), (3, 0))) is None
