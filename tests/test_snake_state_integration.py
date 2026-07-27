"""State-manager integration test for Snake pause and resume timing."""

from __future__ import annotations

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from arcade.state_manager import StateManager
from games.snake.direction import Direction
from states.base_state import BaseState
from states.snake_state import SnakeState


class PauseProbeState(BaseState):
    """Minimal overlay proving active-state-only updates during pause."""

    def handle_event(self, event: pygame.event.Event) -> None:
        del event

    def update(self, delta_time: float) -> None:
        del delta_time

    def render(self, surface: pygame.Surface) -> None:
        del surface


def test_pause_resume_gap_does_not_corrupt_accumulator() -> None:
    pygame.init()
    try:
        manager = StateManager()
        manager.register("snake", lambda state_manager: SnakeState(state_manager))
        manager.register(
            "pause_probe",
            lambda state_manager: PauseProbeState(state_manager),
        )
        manager.replace("snake")

        snake_state = manager.active_state
        assert isinstance(snake_state, SnakeState)
        snake_state.world.movement_interval = 0.2
        snake_state.world.request_direction(Direction.RIGHT)
        original_head = snake_state.world.snapshot().snake_head

        manager.update(0.12)
        manager.push("pause_probe")
        manager.update(5.0)
        manager.pop()
        manager.update(0.07)

        assert snake_state.world.snapshot().snake_head == original_head

        manager.update(0.01)
        assert snake_state.world.snapshot().snake_head == (
            original_head[0] + 1,
            original_head[1],
        )
    finally:
        pygame.quit()
