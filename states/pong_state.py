"""Playable Pong state integrated with the shared application loop."""

from __future__ import annotations

import pygame

from games.pong.pong_world import PongWorld, RoundStatus
from states.base_state import BaseState


class PongState(BaseState):
    """Coordinates Pong input, world updates, rendering, and transitions."""

    BACKGROUND_COLOR = (14, 16, 24)
    FOREGROUND_COLOR = (235, 235, 245)
    MUTED_COLOR = (145, 150, 165)

    def __init__(self, state_manager: object) -> None:
        super().__init__(state_manager)

        self.world = PongWorld()

        self.score_font = pygame.font.Font(None, 64)
        self.message_font = pygame.font.Font(None, 30)

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
        """Temporary reference rendering using immutable world data."""
        surface.fill(self.BACKGROUND_COLOR)

        snapshot = self.world.snapshot()
        width, height = surface.get_size()

        self._draw_center_line(surface, width, height)

        pygame.draw.rect(
            surface,
            self.FOREGROUND_COLOR,
            pygame.Rect(snapshot.player_paddle_bounds),
        )
        pygame.draw.rect(
            surface,
            self.FOREGROUND_COLOR,
            pygame.Rect(snapshot.ai_paddle_bounds),
        )
        pygame.draw.rect(
            surface,
            self.FOREGROUND_COLOR,
            pygame.Rect(snapshot.ball_bounds),
        )

        player_score = self.score_font.render(
            str(snapshot.player_score),
            True,
            self.FOREGROUND_COLOR,
        )
        ai_score = self.score_font.render(
            str(snapshot.ai_score),
            True,
            self.FOREGROUND_COLOR,
        )

        surface.blit(
            player_score,
            player_score.get_rect(center=(width // 2 - 90, 55)),
        )
        surface.blit(
            ai_score,
            ai_score.get_rect(center=(width // 2 + 90, 55)),
        )

        if snapshot.show_serve_prompt:
            prompt = self.message_font.render(
                "Press Space or Enter to serve",
                True,
                self.MUTED_COLOR,
            )
            surface.blit(
                prompt,
                prompt.get_rect(center=(width // 2, height - 48)),
            )

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

    @staticmethod
    def _draw_center_line(
        surface: pygame.Surface,
        width: int,
        height: int,
    ) -> None:
        segment_height = 18
        gap = 14
        x = width // 2 - 2

        for y in range(0, height, segment_height + gap):
            pygame.draw.rect(
                surface,
                (90, 95, 110),
                pygame.Rect(x, y, 4, segment_height),
            )