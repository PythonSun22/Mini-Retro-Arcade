"""Playable Pong state integrated with the shared application loop."""

from __future__ import annotations

import pygame

from games.pong.pong_world import PongWorld, RoundStatus
from states.base_state import BaseState
from ui.pong_view import PongView


class PongState(BaseState):
    """Coordinates Pong input, world updates, rendering, and transitions."""


    def __init__(self, state_manager: object) -> None:
        super().__init__(state_manager)

        self.world = PongWorld()
        self.view = PongView()

        self._move_up = False
        self._move_down = False
        self._game_over_transition_sent = False

    def enter(self, data: dict[str, object] | None = None) -> None:
        """Start with a fresh match."""
        del data
        self.world.restart_match()
        self._clear_input()
        self._game_over_transition_sent = False

    def exit(self) -> None:
        self._clear_input()

    def pause(self) -> None:
        """Stop paddle movement while preserving the match."""
        self._clear_input()

    def resume(self, data: dict[str, object] | None = None) -> None:
        del data
        self._clear_input()

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            self._handle_key_down(event.key)

        elif event.type == pygame.KEYUP:
            self._handle_key_up(event.key)

    def update(self, delta_time: float) -> None:
        direction = float(self._move_down) - float(self._move_up)
        self.world.set_player_direction(direction)
        self.world.update(delta_time)

        if (
            self.world.round_status is RoundStatus.MATCH_COMPLETE
            and not self._game_over_transition_sent
        ):
            self._game_over_transition_sent = True

            self.state_manager.replace(
                "game_over",
                {
                    "game_name": "Pong",
                    "result": self.world.match_result,
                    "player_score": self.world.player_score,
                    "opponent_score": self.world.ai_score,
                    "restart_state": "pong",
                },
            )

    def render(self, surface: pygame.Surface) -> None:
        """Delegate presentation using immutable world data."""
        snapshot = self.world.snapshot()
        self.view.render(surface, snapshot)

    def _handle_key_down(self, key: int) -> None:
        if key in (pygame.K_w, pygame.K_UP):
            self._move_up = True

        elif key in (pygame.K_s, pygame.K_DOWN):
            self._move_down = True

        elif key in (pygame.K_SPACE, pygame.K_RETURN):
            self.world.start_serve()

        elif key == pygame.K_ESCAPE:
            self.state_manager.push("pause")

        elif key in (pygame.K_m, pygame.K_BACKSPACE):
            self.state_manager.replace("main_menu")

    def _handle_key_up(self, key: int) -> None:
        if key in (pygame.K_w, pygame.K_UP):
            self._move_up = False

        elif key in (pygame.K_s, pygame.K_DOWN):
            self._move_down = False

    def _clear_input(self) -> None:
        self._move_up = False
        self._move_down = False
        self.world.set_player_direction(0.0)
