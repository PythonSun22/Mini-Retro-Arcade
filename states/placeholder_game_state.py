"""Reusable placeholder state for unfinished games."""

from __future__ import annotations

import pygame

from states.base_state import BaseState


class PlaceholderGameState(BaseState):
    """Temporary state proving that a game can be launched."""

    def __init__(
        self,
        state_manager: object,
        game_name: str,
    ) -> None:
        super().__init__(state_manager)

        self.game_name = game_name
        self.title_font = pygame.font.Font(None, 64)
        self.message_font = pygame.font.Font(None, 30)

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type != pygame.KEYDOWN:
            return

        if event.key == pygame.K_ESCAPE:
            self.state_manager.push("pause")
            
        if event.key in (pygame.K_BACKSPACE, pygame.K_m):
            self.state_manager.replace("main_menu")

    def update(self, delta_time: float) -> None:
        del delta_time

    def render(self, surface: pygame.Surface) -> None:
        width, height = surface.get_size()

        title = self.title_font.render(
            self.game_name,
            True,
            (235, 235, 245),
        )
        title_rect = title.get_rect(
            center=(width // 2, height // 2 - 50)
        )
        surface.blit(title, title_rect)

        placeholder = self.message_font.render(
            "Placeholder State — No Gameplay Implemented",
            True,
            (170, 175, 190),
        )
        placeholder_rect = placeholder.get_rect(
            center=(width // 2, height // 2 + 20)
        )
        surface.blit(placeholder, placeholder_rect)

        controls = self.message_font.render(
            "Press M or Backspace to return to the menu",
            True,
            (135, 140, 155),
        )
        controls_rect = controls.get_rect(
            center=(width // 2, height // 2 + 70)
        )
        surface.blit(controls, controls_rect)