"""Placeholder main menu state."""

from __future__ import annotations

import pygame

from states.base_state import BaseState


class MainMenuState(BaseState):
    """Minimal menu used to verify state transitions."""

    MENU_ITEMS = (
        ("Pong", "pong"),
        ("Snake", "snake"),
        ("Space Invaders", "space_invaders"),
    )

    def __init__(self, state_manager: object) -> None:
        super().__init__(state_manager)

        self.selected_index = 0
        self.title_font = pygame.font.Font(None, 64)
        self.item_font = pygame.font.Font(None, 38)
        self.help_font = pygame.font.Font(None, 26)

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
        width, height = surface.get_size()

        title = self.title_font.render(
            "Minigame Arcade",
            True,
            (235, 235, 245),
        )
        title_rect = title.get_rect(center=(width // 2, 100))
        surface.blit(title, title_rect)

        start_y = 220
        spacing = 60

        for index, (label, _) in enumerate(self.MENU_ITEMS):
            is_selected = index == self.selected_index
            prefix = "> " if is_selected else "  "

            color = (
                (255, 220, 100)
                if is_selected
                else (190, 195, 210)
            )

            item = self.item_font.render(
                f"{prefix}{label}",
                True,
                color,
            )
            item_rect = item.get_rect(
                center=(width // 2, start_y + index * spacing)
            )
            surface.blit(item, item_rect)

        help_text = self.help_font.render(
            "Arrow keys or W/S to select — Enter to launch",
            True,
            (135, 140, 155),
        )
        help_rect = help_text.get_rect(
            center=(width // 2, height - 55)
        )
        surface.blit(help_text, help_rect)