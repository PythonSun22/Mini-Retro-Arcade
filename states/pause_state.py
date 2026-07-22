"""Shared pause overlay state."""

from __future__ import annotations
from ui.menu_view import MenuView

import pygame

from states.base_state import BaseState


class PauseState(BaseState):
    """Overlay that pauses the active game state."""

    MENU_ITEMS = (
        ("Resume", "resume"),
        ("Return to Main Menu", "main_menu"),
    )

    OVERLAY_COLOR = (0, 0, 0, 165)

    def __init__(self, state_manager: object) -> None:
        super().__init__(state_manager)

        self.selected_index = 0
        self.menu_view = MenuView(
            title="Paused",
            subtitle="Game suspended",
            status_text="",
            help_text="Escape resumes — Arrow keys and Enter select",
            clear_background=False,
        )

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type != pygame.KEYDOWN:
            return

        if event.key in (pygame.K_UP, pygame.K_w):
            self.selected_index = (
                self.selected_index - 1
            ) % len(self.MENU_ITEMS)

        elif event.key in (pygame.K_DOWN, pygame.K_s):
            self.selected_index = (
                self.selected_index + 1
            ) % len(self.MENU_ITEMS)

        elif event.key == pygame.K_ESCAPE:
            self.state_manager.pop()

        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
            _, action = self.MENU_ITEMS[self.selected_index]

            if action == "resume":
                self.state_manager.pop()
            elif action == "main_menu":
                self.state_manager.replace("main_menu")

    def update(self, delta_time: float) -> None:
        del delta_time

    def render(self, surface: pygame.Surface) -> None:

        overlay = pygame.Surface(
            surface.get_size(),
            flags=pygame.SRCALPHA,
        )
        overlay.fill(self.OVERLAY_COLOR)
        surface.blit(overlay, (0, 0))

        labels = [label for label, _ in self.MENU_ITEMS]
        self.menu_view.render(
            surface, 
            labels, 
            self.selected_index,
        )
        