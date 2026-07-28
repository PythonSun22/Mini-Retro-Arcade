"""Immutable Snake completion result."""

from __future__ import annotations

from dataclasses import dataclass

from games.snake.snake_world import GameOverReason, MatchResult


@dataclass(frozen=True)
class SnakeResult:
    """Final authoritative data required after a Snake run."""

    score: int
    speed_level: int
    completion_reason: GameOverReason
    outcome: MatchResult
    grid_completed: bool

    @classmethod
    def create(
        cls,
        *,
        score: int,
        speed_level: int,
        completion_reason: GameOverReason,
        outcome: MatchResult,
    ) -> "SnakeResult":
        """Create a validated result from completed Snake world data."""
        if outcome is MatchResult.NONE:
            raise ValueError("A completed Snake run must have a final outcome.")
        if completion_reason is GameOverReason.NONE:
            raise ValueError("A completed Snake run must have a completion reason.")

        grid_completed = completion_reason is GameOverReason.GRID_COMPLETED
        if grid_completed != (outcome is MatchResult.WIN):
            raise ValueError("Snake outcome and completion reason are inconsistent.")

        return cls(
            score=score,
            speed_level=speed_level,
            completion_reason=completion_reason,
            outcome=outcome,
            grid_completed=grid_completed,
        )
