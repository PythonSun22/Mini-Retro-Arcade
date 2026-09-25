"""World model coordinating the Pong domain."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
import random

from games.pong.ball import Ball
from games.pong.paddle import AIPaddle, Paddle
from games.pong.pong_rules import PongRules


class RoundStatus(Enum):
    """Current phase of a Pong round."""

    WAITING_TO_SERVE = auto()
    ACTIVE = auto()
    MATCH_COMPLETE = auto()


@dataclass(frozen=True)
class PongSnapshot:
    """Read-only presentation data for rendering and UI."""

    player_score: int
    ai_score: int
    winning_score: int

    ball_position: tuple[float, float]
    ball_bounds: tuple[int, int, int, int]

    player_paddle_position: tuple[float, float]
    player_paddle_bounds: tuple[int, int, int, int]

    ai_paddle_position: tuple[float, float]
    ai_paddle_bounds: tuple[int, int, int, int]

    round_status: RoundStatus
    match_result: str | None
    show_serve_prompt: bool


class PongWorld:
    """Owns Pong entities, scores, and match state."""

    WIDTH = 960
    HEIGHT = 540

    PADDLE_WIDTH = 18
    PADDLE_HEIGHT = 110
    PADDLE_MARGIN = 42

    PLAYER_SPEED = 430.0
    AI_SPEED = 285.0

    BALL_SIZE = 18
    BALL_SPEED_X = 390.0
    BALL_SPEED_Y = 310.0

    DEFAULT_WINNING_SCORE = 5

    def __init__(
        self,
        winning_score: int = DEFAULT_WINNING_SCORE,
        random_source: random.Random | None = None,
    ) -> None:
        self.random_source = random_source or random.Random()

        centered_paddle_y = (
            self.HEIGHT - self.PADDLE_HEIGHT
        ) / 2.0

        self.player_paddle = Paddle(
            x=float(self.PADDLE_MARGIN),
            y=centered_paddle_y,
            width=self.PADDLE_WIDTH,
            height=self.PADDLE_HEIGHT,
            speed=self.PLAYER_SPEED,
            playfield_height=self.HEIGHT,
        )

        self.ai_paddle = AIPaddle(
            x=float(
                self.WIDTH
                - self.PADDLE_MARGIN
                - self.PADDLE_WIDTH
            ),
            y=centered_paddle_y,
            width=self.PADDLE_WIDTH,
            height=self.PADDLE_HEIGHT,
            speed=self.AI_SPEED,
            playfield_height=self.HEIGHT,
            tracking_dead_zone=22.0,
        )

        self.ball = Ball(
            x=0.0,
            y=0.0,
            size=self.BALL_SIZE,
            velocity_x=0.0,
            velocity_y=0.0,
        )

        self.rules = PongRules(
            playfield_width=self.WIDTH,
            playfield_height=self.HEIGHT,
            winning_score=winning_score,
            ball_speed_x=self.BALL_SPEED_X,
            ball_speed_y=self.BALL_SPEED_Y,
            random_source=self.random_source,
        )

        self.player_score = 0
        self.ai_score = 0
        self.round_status = RoundStatus.WAITING_TO_SERVE
        self.match_result: str | None = None

        self._reset_ball_to_center()

    def set_player_direction(self, direction: float) -> None:
        self.player_paddle.set_direction(direction)

    def start_serve(self) -> bool:
        """Begin play if the world is waiting for a serve."""
        if self.round_status is not RoundStatus.WAITING_TO_SERVE:
            return False

        velocity_x, velocity_y = (
            self.rules.create_serve_velocity()
        )

        self.ball.velocity_x = velocity_x
        self.ball.velocity_y = velocity_y
        self.round_status = RoundStatus.ACTIVE
        return True

    def update(self, delta_time: float) -> None:
        """Advance the active match by one frame."""
        if delta_time < 0.0:
            raise ValueError("Delta time cannot be negative.")

        self.player_paddle.update(delta_time)

        if self.round_status is not RoundStatus.ACTIVE:
            return

        self.ai_paddle.react_to_ball(
            self.ball.center_y,
            delta_time,
        )

        self.ball.update(delta_time)

        self.rules.resolve_wall_collision(self.ball)

        if self.ball.velocity_x < 0.0:
            self.rules.resolve_paddle_collision(
                self.ball,
                self.player_paddle,
                horizontal_direction=1,
            )
        else:
            self.rules.resolve_paddle_collision(
                self.ball,
                self.ai_paddle,
                horizontal_direction=-1,
            )

        score_result = self.rules.detect_score(self.ball)

        if score_result.player_scored:
            self.player_score += 1
            self._finish_round()
        elif score_result.ai_scored:
            self.ai_score += 1
            self._finish_round()

    def restart_match(self) -> None:
        """Reset the world to a completely fresh match."""
        self.player_score = 0
        self.ai_score = 0
        self.match_result = None
        self.round_status = RoundStatus.WAITING_TO_SERVE

        centered_paddle_y = (
            self.HEIGHT - self.PADDLE_HEIGHT
        ) / 2.0

        self.player_paddle.reset(centered_paddle_y)
        self.ai_paddle.reset(centered_paddle_y)
        self._reset_ball_to_center()

    def snapshot(self) -> PongSnapshot:
        """Return immutable presentation data."""
        player_bounds = self.player_paddle.bounds
        ai_bounds = self.ai_paddle.bounds
        ball_bounds = self.ball.bounds

        return PongSnapshot(
            player_score=self.player_score,
            ai_score=self.ai_score,
            winning_score=self.rules.winning_score,
            ball_position=(self.ball.x, self.ball.y),
            ball_bounds=(
                ball_bounds.x,
                ball_bounds.y,
                ball_bounds.width,
                ball_bounds.height,
            ),
            player_paddle_position=(
                self.player_paddle.x,
                self.player_paddle.y,
            ),
            player_paddle_bounds=(
                player_bounds.x,
                player_bounds.y,
                player_bounds.width,
                player_bounds.height,
            ),
            ai_paddle_position=(
                self.ai_paddle.x,
                self.ai_paddle.y,
            ),
            ai_paddle_bounds=(
                ai_bounds.x,
                ai_bounds.y,
                ai_bounds.width,
                ai_bounds.height,
            ),
            round_status=self.round_status,
            match_result=self.match_result,
            show_serve_prompt=(
                self.round_status
                is RoundStatus.WAITING_TO_SERVE
            ),
        )

    def _finish_round(self) -> None:
        self.match_result = self.rules.match_result(
            self.player_score,
            self.ai_score,
        )

        if self.match_result is not None:
            self.round_status = RoundStatus.MATCH_COMPLETE
            self.ball.velocity_x = 0.0
            self.ball.velocity_y = 0.0
            return

        self.round_status = RoundStatus.WAITING_TO_SERVE
        self._reset_ball_to_center()

    def _reset_ball_to_center(self) -> None:
        centered_x = (self.WIDTH - self.BALL_SIZE) / 2.0
        centered_y = (self.HEIGHT - self.BALL_SIZE) / 2.0

        self.ball.reset(
            x=centered_x,
            y=centered_y,
            velocity_x=0.0,
            velocity_y=0.0,
        )
