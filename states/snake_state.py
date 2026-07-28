"""Thin Snake state integrated with the shared application loop."""

from __future__ import annotations

from typing import Protocol

import pygame

from games.snake.direction import Direction
from games.snake.snake_result import SnakeResult
from games.snake.snake_world import MatchStatus, SnakeWorld
from states.base_state import BaseState
from states.game_over_state import GameOverContext


class SnakeGameplayView(Protocol):
    """Presentation dependency supplied by application bootstrap."""

    def render(self, surface: pygame.Surface, snapshot: object) -> None:
        ...


class SnakeState(BaseState):
    """Translate input, update SnakeWorld, and delegate presentation."""

    def __init__(
        self,
        state_manager: object,
        view: SnakeGameplayView,
    ) -> None:
        super().__init__(state_manager)

        self.world = SnakeWorld()
        self.view = view
        self._game_over_transition_sent = False

    def enter(self, data: dict[str, object] | None = None) -> None:
        del data
        self.world.restart()
        self._game_over_transition_sent = False

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type != pygame.KEYDOWN:
            return

        direction = self._direction_for_key(event.key)
        if direction is not None:
            self.world.request_direction(direction)

        elif event.key == pygame.K_ESCAPE:
            self.state_manager.push("pause")

        elif event.key in (pygame.K_m, pygame.K_BACKSPACE):
            self.state_manager.replace("main_menu")

    def update(self, delta_time: float) -> None:
        self.world.update(delta_time)

        if (
            self.world.match_status is MatchStatus.COMPLETED
            and not self._game_over_transition_sent
        ):
            self._game_over_transition_sent = True
            result = SnakeResult.create(
                score=self.world.score,
                speed_level=self.world.speed_level,
                completion_reason=self.world.game_over_reason,
                outcome=self.world.match_result,
            )
            self.state_manager.replace(
                "game_over",
                {
                    "context": GameOverContext(
                        result=result,
                        restart_state="snake",
                    ),
                },
            )

    def render(self, surface: pygame.Surface) -> None:
        """Delegate presentation using immutable world data."""
        snapshot = self.world.snapshot()
        self.view.render(surface, snapshot)

    @staticmethod
    def _direction_for_key(key: int) -> Direction | None:
        mapping = {
            pygame.K_UP: Direction.UP,
            pygame.K_w: Direction.UP,
            pygame.K_DOWN: Direction.DOWN,
            pygame.K_s: Direction.DOWN,
            pygame.K_LEFT: Direction.LEFT,
            pygame.K_a: Direction.LEFT,
            pygame.K_RIGHT: Direction.RIGHT,
            pygame.K_d: Direction.RIGHT,
        }
        return mapping.get(key)
