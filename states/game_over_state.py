"""Shared game-over state."""

from __future__ import annotations

from typing import Any

import pygame

from ui.menu_view import MenuView

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

        self.menu_view = MenuView(
            title="Game Complete",
            subtitle="Final Result",
            status_text="",
            help_text="Arrow keys select — Enter confirms — Escape returns",
        )

        self.score_font = pygame.font.Font(None, 42)

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

        self.menu_view.title = f"{self.game_name} Complete"

        if self.result == "player":
            self.menu_view.status_text = "You Win"
        elif self.result is None:
            self.menu_view.status_text = "Match Complete"
        else:
            self.menu_view.status_text = "AI Wins"  

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
        labels = [label for label, _ in self.MENU_ITEMS]

        self.menu_view.render(
            surface,
            labels,
            self.selected_index,
        )

        width, height = surface.get_size()

        score = self.score_font.render(
            f"{self.player_score} - {self.opponent_score}",
            True,
            self.menu_view.theme.text_secondary,
        )

        surface.blit(
            score,
            score.get_rect(center=(width // 2, height // 2 - 85)),
        )