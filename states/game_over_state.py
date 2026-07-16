"""Shared game-over state."""

from __future__ import annotations

from typing import Any

import pygame

from states.base_state import BaseState


class GameOverState(BaseState):
    """Displays final match data and routes restart or menu actions."""

    MENU_ITEMS = (
        ("Restart", "restart"),
        ("Return to Main Menu", "main_menu"),
    )

    def __init__(self, state_manager: object) -> None:
        super().__init__(state_manager)

        self.selected_index = 0

        self.game_name = "Game"
        self.result: str | None = None
        self.player_score = 0
        self.opponent_score = 0
        self.restart_state = "main_menu"

        self.title_font = pygame.font.Font(None, 68)
        self.result_font = pygame.font.Font(None, 42)
        self.item_font = pygame.font.Font(None, 34)

    def enter(self, data: dict[str, Any] | None = None) -> None:
        data = data or {}

        self.selected_index = 0
        self.game_name = str(data.get("game_name", "Game"))
        self.result = (
            str(data["result"])
            if data.get("result") is not None
            else None
        )
        self.player_score = int(data.get("player_score", 0))
        self.opponent_score = int(data.get("opponent_score", 0))
        self.restart_state = str(
            data.get("restart_state", "main_menu")
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

        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
            _, action = self.MENU_ITEMS[self.selected_index]

            if action == "restart":
                self.state_manager.replace(self.restart_state)
            else:
                self.state_manager.replace("main_menu")

        elif event.key == pygame.K_ESCAPE:
            self.state_manager.replace("main_menu")

    def update(self, delta_time: float) -> None:
        del delta_time

    def render(self, surface: pygame.Surface) -> None:
        surface.fill((18, 20, 28))

        width, height = surface.get_size()

        title = self.title_font.render(
            f"{self.game_name} Complete",
            True,
            (240, 240, 248),
        )
        surface.blit(
            title,
            title.get_rect(center=(width // 2, 105)),
        )

        result_text = (
            "You Win"
            if self.result == "player"
            else "AI Wins"
        )
        result = self.result_font.render(
            result_text,
            True,
            (255, 220, 100),
        )
        surface.blit(
            result,
            result.get_rect(center=(width // 2, 185)),
        )

        score = self.result_font.render(
            f"{self.player_score} - {self.opponent_score}",
            True,
            (190, 195, 210),
        )
        surface.blit(
            score,
            score.get_rect(center=(width // 2, 240)),
        )

        start_y = 340

        for index, (label, _) in enumerate(self.MENU_ITEMS):
            selected = index == self.selected_index
            prefix = "> " if selected else "  "
            color = (
                (255, 220, 100)
                if selected
                else (190, 195, 210)
            )

            item = self.item_font.render(
                f"{prefix}{label}",
                True,
                color,
            )
            surface.blit(
                item,
                item.get_rect(
                    center=(width // 2, start_y + index * 55)
                ),
            )