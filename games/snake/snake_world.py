"""World model coordinating the Snake vertical slice."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto

from games.snake.direction import Direction
from games.snake.food import Food
from games.snake.grid import Grid, GridPosition
from games.snake.snake import Snake
from games.snake.snake_rules import RandomSource, SnakeRules


class MatchStatus(Enum):
    """Current phase of a Snake run."""

    WAITING_TO_START = auto()
    ACTIVE = auto()
    COMPLETED = auto()


class MatchResult(Enum):
    """Final run result, reserved for later completion logic."""

    NONE = auto()
    LOSS = auto()
    WIN = auto()


class GameOverReason(Enum):
    """Completion reason, reserved for later collision integration."""

    NONE = auto()
    WALL_COLLISION = auto()
    SELF_COLLISION = auto()
    GRID_COMPLETED = auto()


@dataclass(frozen=True)
class SnakeSnapshot:
    """Immutable presentation contract for SnakeSnapshot v1."""

    version: int
    grid_width: int
    grid_height: int
    snake_body: tuple[GridPosition, ...]
    snake_head: GridPosition
    current_direction: Direction
    food_position: GridPosition | None
    score: int
    food_count: int
    movement_interval: float
    speed_level: int
    match_status: MatchStatus
    match_result: MatchResult
    game_over_reason: GameOverReason
    show_start_prompt: bool


class SnakeWorld:
    """Owns Snake entities, fixed-step timing, and snapshot data."""

    DEFAULT_MOVEMENT_INTERVAL = 0.18
    DEFAULT_SNAKE_LENGTH = 3
    MAX_STEPS_PER_UPDATE = 8
    SNAPSHOT_VERSION = 1

    def __init__(
        self,
        grid: Grid | None = None,
        movement_interval: float = DEFAULT_MOVEMENT_INTERVAL,
        random_source: RandomSource | None = None,
    ) -> None:
        if movement_interval <= 0.0:
            raise ValueError("Movement interval must be greater than zero.")

        self.grid = grid or Grid()
        self.movement_interval = movement_interval
        self.rules = SnakeRules(self.grid, random_source=random_source)

        initial_body = self._create_initial_body()
        self.snake = Snake(list(initial_body), Direction.RIGHT)

        food_position = self.rules.choose_food_position(initial_body)
        if food_position is None:
            raise ValueError("Grid must contain space for initial food.")

        self.food = Food(food_position)
        self.score = 0
        self.food_count = 0
        self.speed_level = 1
        self.match_status = MatchStatus.WAITING_TO_START
        self.match_result = MatchResult.NONE
        self.game_over_reason = GameOverReason.NONE

        self._pending_direction: Direction | None = None
        self._accumulator = 0.0

    def restart(self) -> None:
        """Reset the world to a fresh waiting state."""
        initial_body = self._create_initial_body()
        self.snake.reset(initial_body, Direction.RIGHT)

        food_position = self.rules.choose_food_position(initial_body)
        if food_position is None:
            raise ValueError("Grid must contain space for initial food.")

        self.food.position = food_position
        self.score = 0
        self.food_count = 0
        self.speed_level = 1
        self.match_status = MatchStatus.WAITING_TO_START
        self.match_result = MatchResult.NONE
        self.game_over_reason = GameOverReason.NONE
        self._pending_direction = None
        self._accumulator = 0.0

    def request_direction(self, direction: Direction) -> bool:
        """Buffer one valid direction change for the next logical step.

        The first accepted request is retained until movement occurs. This
        prevents multiple key presses within one frame from producing a hidden
        180-degree reversal.
        """
        if self.match_status is MatchStatus.COMPLETED:
            return False

        if self._pending_direction is not None:
            return False

        if not self.rules.is_valid_direction_change(
            self.snake.direction,
            direction,
        ):
            return False

        if direction is not self.snake.direction:
            self._pending_direction = direction

        if self.match_status is MatchStatus.WAITING_TO_START:
            self.match_status = MatchStatus.ACTIVE

        return True

    def update(self, delta_time: float) -> None:
        """Advance movement at fixed logical intervals."""
        if delta_time < 0.0:
            raise ValueError("Delta time cannot be negative.")

        if self.match_status is not MatchStatus.ACTIVE:
            return

        self._accumulator += delta_time
        steps = 0

        while (
            self._accumulator >= self.movement_interval
            and steps < self.MAX_STEPS_PER_UPDATE
        ):
            self._advance_one_step()
            self._accumulator -= self.movement_interval
            steps += 1

        if steps == self.MAX_STEPS_PER_UPDATE:
            self._accumulator %= self.movement_interval

    def snapshot(self) -> SnakeSnapshot:
        """Return immutable presentation data."""
        snake_body = tuple(self.snake.body)

        return SnakeSnapshot(
            version=self.SNAPSHOT_VERSION,
            grid_width=self.grid.width,
            grid_height=self.grid.height,
            snake_body=snake_body,
            snake_head=snake_body[0],
            current_direction=self.snake.direction,
            food_position=self.food.position,
            score=self.score,
            food_count=self.food_count,
            movement_interval=self.movement_interval,
            speed_level=self.speed_level,
            match_status=self.match_status,
            match_result=self.match_result,
            game_over_reason=self.game_over_reason,
            show_start_prompt=(
                self.match_status is MatchStatus.WAITING_TO_START
            ),
        )

    def _advance_one_step(self) -> None:
        if self._pending_direction is not None:
            self.snake.direction = self._pending_direction
            self._pending_direction = None

        new_head = self.rules.next_head(
            self.snake.head,
            self.snake.direction,
        )
        self.snake.move_to(new_head)

    def _create_initial_body(self) -> tuple[GridPosition, ...]:
        if self.grid.width < self.DEFAULT_SNAKE_LENGTH + 1:
            raise ValueError(
                "Grid width must fit the initial snake and at least one food cell."
            )

        center_x = self.grid.width // 2
        center_y = self.grid.height // 2

        return tuple(
            (center_x - offset, center_y)
            for offset in range(self.DEFAULT_SNAKE_LENGTH)
        )
