"""Thin Snake state integrated with the shared application loop."""

from __future__ import annotations

import pygame

from games.snake.direction import Direction
from games.snake.snake_world import SnakeWorld
from states.base_state import BaseState
from ui.snake_view import SnakeView


class SnakeState(BaseState):
    """Translate input, update SnakeWorld, and delegate presentation."""

    def __init__(self, state_manager: object) -> None:
        super().__init__(state_manager)

        self.world = SnakeWorld()
        self.view = SnakeView()

    def enter(self, data: dict[str, object] | None = None) -> None:
        del data
        self.world.restart()

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
