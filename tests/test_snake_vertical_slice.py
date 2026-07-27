"""Focused tests for the authorized Snake backend vertical slice."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
import pytest

from games.snake.direction import Direction
from games.snake.grid import Grid
from games.snake.snake_world import MatchStatus, SnakeSnapshot, SnakeWorld


class FirstChoiceRandom:
    """Deterministic random source for food-placement tests."""

    @staticmethod
    def choice(sequence):
        return sequence[0]


def make_world(interval: float = 0.2) -> SnakeWorld:
    return SnakeWorld(
        grid=Grid(width=12, height=8),
        movement_interval=interval,
        random_source=FirstChoiceRandom(),
    )


def test_world_initializes_snake_and_unoccupied_food() -> None:
    world = make_world()
    snapshot = world.snapshot()

    assert snapshot.match_status is MatchStatus.WAITING_TO_START
    assert snapshot.show_start_prompt is True
    assert len(snapshot.snake_body) == 3
    assert snapshot.snake_head == snapshot.snake_body[0]
    assert snapshot.food_position not in snapshot.snake_body
    assert snapshot.grid_width == 12
    assert snapshot.grid_height == 8


def test_world_does_not_move_before_valid_start_input() -> None:
    world = make_world()
    initial_body = world.snapshot().snake_body

    world.update(1.0)

    assert world.snapshot().snake_body == initial_body


def test_opposite_direction_is_rejected_and_does_not_start() -> None:
    world = make_world()

    accepted = world.request_direction(Direction.LEFT)

    assert accepted is False
    assert world.snapshot().match_status is MatchStatus.WAITING_TO_START
    assert world.snapshot().current_direction is Direction.RIGHT


def test_valid_direction_starts_and_applies_on_next_fixed_step() -> None:
    world = make_world(interval=0.2)
    original_head = world.snapshot().snake_head

    assert world.request_direction(Direction.UP) is True
    world.update(0.19)

    assert world.snapshot().snake_head == original_head
    assert world.snapshot().current_direction is Direction.RIGHT

    world.update(0.01)
    snapshot = world.snapshot()

    assert snapshot.snake_head == (original_head[0], original_head[1] - 1)
    assert snapshot.current_direction is Direction.UP
    assert snapshot.match_status is MatchStatus.ACTIVE
    assert snapshot.show_start_prompt is False


def test_only_one_turn_is_buffered_per_logical_step() -> None:
    world = make_world(interval=0.2)

    assert world.request_direction(Direction.UP) is True
    assert world.request_direction(Direction.LEFT) is False

    world.update(0.2)

    assert world.snapshot().current_direction is Direction.UP


def test_fixed_step_accumulator_preserves_partial_time() -> None:
    world = make_world(interval=0.2)
    world.request_direction(Direction.RIGHT)
    original_head = world.snapshot().snake_head

    world.update(0.12)
    assert world.snapshot().snake_head == original_head

    world.update(0.08)
    assert world.snapshot().snake_head == (original_head[0] + 1, original_head[1])


def test_snapshot_is_frozen_and_detached_from_mutable_body() -> None:
    world = make_world()
    snapshot = world.snapshot()

    assert isinstance(snapshot, SnakeSnapshot)
    assert isinstance(snapshot.snake_body, tuple)

    with pytest.raises(FrozenInstanceError):
        snapshot.score = 99  # type: ignore[misc]

    world.request_direction(Direction.RIGHT)
    world.update(world.movement_interval)

    assert snapshot.snake_body != world.snapshot().snake_body


def test_negative_delta_time_is_rejected() -> None:
    world = make_world()

    with pytest.raises(ValueError, match="Delta time"):
        world.update(-0.01)
