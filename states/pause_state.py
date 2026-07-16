"""Shared pause overlay state."""

from __future__ import annotations

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
        self.title_font = pygame.font.Font(None, 68)
        self.item_font = pygame.font.Font(None, 38)
        self.help_font = pygame.font.Font(None, 25)

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
        width, height = surface.get_size()

        overlay = pygame.Surface(
            surface.get_size(),
            flags=pygame.SRCALPHA,
        )
        overlay.fill(self.OVERLAY_COLOR)
        surface.blit(overlay, (0, 0))

        title = self.title_font.render(
            "Paused",
            True,
            (245, 245, 250),
        )
        title_rect = title.get_rect(
            center=(width // 2, height // 2 - 110)
        )
        surface.blit(title, title_rect)

        start_y = height // 2 - 20
        spacing = 58

        for index, (label, _) in enumerate(self.MENU_ITEMS):
            is_selected = index == self.selected_index
            prefix = "> " if is_selected else "  "

            color = (
                (255, 220, 100)
                if is_selected
                else (195, 200, 215)
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
            "Escape resumes — Arrow keys and Enter select",
            True,
            (155, 160, 175),
        )
        help_rect = help_text.get_rect(
            center=(width // 2, height - 55)
        )
        surface.blit(help_text, help_rect)