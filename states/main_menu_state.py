"""Main menu state."""

from __future__ import annotations

import pygame

from states.base_state import BaseState
from ui.menu_view import MenuView


class MainMenuState(BaseState):
    """Primary game-selection menu."""

    MENU_ITEMS = (
        ("Pong", "pong"),
        ("Snake", "snake"),
        ("Space Invaders", "space_invaders"),
    )

    def __init__(self, state_manager: object) -> None:
        super().__init__(state_manager)

        self.selected_index = 0
        self.view = MenuView(
            title="Minigame Arcade",
            subtitle="SELECT A CABINET",
            help_text="Arrow keys or W/S to select  •  Enter to launch",
        )

    def enter(self, data: dict[str, object] | None = None) -> None:
        del data
        self.selected_index = 0

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

        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
            _, state_name = self.MENU_ITEMS[self.selected_index]
            self.state_manager.replace(state_name)

        elif event.key == pygame.K_1:
            self.state_manager.replace("pong")

        elif event.key == pygame.K_2:
            self.state_manager.replace("snake")

        elif event.key == pygame.K_3:
            self.state_manager.replace("space_invaders")

    def update(self, delta_time: float) -> None:
        del delta_time

    def render(self, surface: pygame.Surface) -> None:
        labels = [label for label, _ in self.MENU_ITEMS]
        self.view.render(surface, labels, self.selected_index)
