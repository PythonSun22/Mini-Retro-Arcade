"""Immutable Space Invaders completion result."""
from __future__ import annotations
from dataclasses import dataclass

from games.space_invaders.space_invaders_snapshot import CompletionReason, MatchOutcome


@dataclass(frozen=True)
class SpaceInvadersResult:
    score: int
    waves_completed: int
    enemies_destroyed: int
    remaining_lives: int
    outcome: MatchOutcome
    completion_reason: CompletionReason

    @classmethod
    def create(
        cls,
        *,
        score: int,
        waves_completed: int,
        enemies_destroyed: int,
        remaining_lives: int,
        outcome: MatchOutcome,
        completion_reason: CompletionReason,
    ) -> "SpaceInvadersResult":
        if min(score, waves_completed, enemies_destroyed, remaining_lives) < 0:
            raise ValueError("Space Invaders result values cannot be negative.")
        if outcome is MatchOutcome.NONE:
            raise ValueError("A completed run requires a final outcome.")
        if completion_reason is CompletionReason.NONE:
            raise ValueError("A completed run requires a completion reason.")
        victory = completion_reason is CompletionReason.ALL_WAVES_CLEARED
        if victory != (outcome is MatchOutcome.VICTORY):
            raise ValueError("Outcome and completion reason are inconsistent.")
        return cls(
            score=score,
            waves_completed=waves_completed,
            enemies_destroyed=enemies_destroyed,
            remaining_lives=remaining_lives,
            outcome=outcome,
            completion_reason=completion_reason,
        )
