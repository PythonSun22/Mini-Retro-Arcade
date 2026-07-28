"""Immutable Pong completion result."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto


class PongWinner(Enum):
    """Side that won a completed Pong match."""

    PLAYER = auto()
    AI = auto()


@dataclass(frozen=True)
class PongResult:
    """Final authoritative data required after a Pong match."""

    player_score: int
    ai_score: int
    winner: PongWinner

    @classmethod
    def create(
        cls,
        *,
        player_score: int,
        ai_score: int,
        match_result: str | None,
    ) -> "PongResult":
        """Create a typed result from the existing Pong world contract."""
        if match_result == "player":
            winner = PongWinner.PLAYER
        elif match_result == "ai":
            winner = PongWinner.AI
        else:
            raise ValueError("A completed Pong match must identify a winner.")

        return cls(
            player_score=player_score,
            ai_score=ai_score,
            winner=winner,
        )
