"""Authoritative rule set for Pong."""

from __future__ import annotations

from dataclasses import dataclass
import random
from typing import Protocol

from games.pong.ball import Ball
from games.pong.paddle import Paddle


class RandomSource(Protocol):
    """Minimal random interface required by Pong rules."""

    def choice(self, sequence: tuple[int, ...]) -> int:
        ...


@dataclass(frozen=True)
class ScoreResult:
    """Result returned when checking whether a goal occurred."""

    player_scored: bool = False
    ai_scored: bool = False

    @property
    def goal_occurred(self) -> bool:
        return self.player_scored or self.ai_scored


class PongRules:
    """Collision, scoring, serve, and match-completion rules."""

    def __init__(
        self,
        playfield_width: int,
        playfield_height: int,
        winning_score: int,
        ball_speed_x: float,
        ball_speed_y: float,
        random_source: RandomSource | None = None,
    ) -> None:
        if winning_score <= 0:
            raise ValueError("Winning score must be greater than zero.")

        self.playfield_width = playfield_width
        self.playfield_height = playfield_height
        self.winning_score = winning_score
        self.ball_speed_x = abs(ball_speed_x)
        self.ball_speed_y = abs(ball_speed_y)
        self.random_source = random_source or random.Random()

    def resolve_wall_collision(self, ball: Ball) -> None:
        """Reflect the ball from the top and bottom walls."""
        if ball.y <= 0.0 and ball.velocity_y < 0.0:
            ball.y = 0.0
            ball.velocity_y *= -1.0

        maximum_y = self.playfield_height - ball.size

        if ball.y >= maximum_y and ball.velocity_y > 0.0:
            ball.y = float(maximum_y)
            ball.velocity_y *= -1.0

    def resolve_paddle_collision(
        self,
        ball: Ball,
        paddle: Paddle,
        horizontal_direction: int,
    ) -> bool:
        """Reflect the ball when it enters a paddle.

        horizontal_direction must be 1 for a left-side paddle and
        -1 for a right-side paddle.
        """
        if horizontal_direction not in (-1, 1):
            raise ValueError("Horizontal direction must be -1 or 1.")

        if not ball.bounds.colliderect(paddle.bounds):
            return False

        ball.velocity_x = abs(ball.velocity_x) * horizontal_direction

        relative_impact = (
            ball.center_y - paddle.center_y
        ) / (paddle.height / 2.0)

        relative_impact = max(-1.0, min(1.0, relative_impact))
        ball.velocity_y = relative_impact * self.ball_speed_y

        if horizontal_direction > 0:
            ball.x = float(paddle.bounds.right)
        else:
            ball.x = float(paddle.bounds.left - ball.size)

        return True

    def detect_score(self, ball: Ball) -> ScoreResult:
        """Return which side scored, if any."""
        if ball.bounds.right < 0:
            return ScoreResult(ai_scored=True)

        if ball.bounds.left > self.playfield_width:
            return ScoreResult(player_scored=True)

        return ScoreResult()

    def create_serve_velocity(
        self,
        horizontal_direction: int | None = None,
    ) -> tuple[float, float]:
        """Create a deterministic-testable serve velocity."""
        if horizontal_direction is None:
            horizontal_direction = self.random_source.choice((-1, 1))

        if horizontal_direction not in (-1, 1):
            raise ValueError("Serve direction must be -1 or 1.")

        vertical_direction = self.random_source.choice((-1, 1))

        return (
            self.ball_speed_x * horizontal_direction,
            self.ball_speed_y * 0.5 * vertical_direction,
        )

    def is_match_complete(
        self,
        player_score: int,
        ai_score: int,
    ) -> bool:
        return (
            player_score >= self.winning_score
            or ai_score >= self.winning_score
        )

    def match_result(
        self,
        player_score: int,
        ai_score: int,
    ) -> str | None:
        if player_score >= self.winning_score:
            return "player"

        if ai_score >= self.winning_score:
            return "ai"

        return None