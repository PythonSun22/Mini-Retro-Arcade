"""Game-specific completed-match presentation for Pong."""

from __future__ import annotations

from collections.abc import Sequence

import pygame

from games.pong.pong_result import PongResult, PongWinner
from ui.theme import ArcadeTheme, DEFAULT_THEME


class PongResultView:
    """Render immutable Pong results without owning application behavior."""

    BACKGROUND_COLOR = (10, 13, 22)
    PLAYER_COLOR = (106, 205, 255)
    AI_COLOR = (255, 211, 92)
    VICTORY_COLOR = (112, 224, 150)
    DEFEAT_COLOR = (239, 112, 123)
    GRID_COLOR = (19, 24, 38)

    def __init__(self, theme: ArcadeTheme = DEFAULT_THEME) -> None:
        self.theme = theme
        self.title_font = pygame.font.Font(None, 72)
        self.subtitle_font = pygame.font.Font(None, 30)
        self.score_font = pygame.font.Font(None, 82)
        self.label_font = pygame.font.Font(None, 22)
        self.action_font = pygame.font.Font(None, 34)
        self.help_font = pygame.font.Font(None, 22)

    def render(
        self,
        surface: pygame.Surface,
        result: object,
        actions: tuple[tuple[str, str], ...],
        selected_index: int,
    ) -> None:
        """Render one completed Pong match and the shared action choices."""
        if not isinstance(result, PongResult):
            raise TypeError("PongResultView requires a PongResult.")

        width, height = surface.get_size()
        surface.fill(self.BACKGROUND_COLOR)
        self._draw_background(surface, width, height)

        panel_width = min(620, max(320, width - 48))
        panel_height = min(430, max(360, height - 54))
        panel = pygame.Rect(0, 0, panel_width, panel_height)
        panel.center = (width // 2, height // 2)

        pygame.draw.rect(
            surface,
            self.theme.shadow,
            panel.move(0, 9),
            border_radius=self.theme.panel_radius,
        )
        pygame.draw.rect(
            surface,
            self.theme.panel,
            panel,
            border_radius=self.theme.panel_radius,
        )
        pygame.draw.rect(
            surface,
            self.theme.panel_border,
            panel,
            width=2,
            border_radius=self.theme.panel_radius,
        )

        victory = result.winner is PongWinner.PLAYER
        heading = "VICTORY" if victory else "MATCH LOST"
        heading_color = self.VICTORY_COLOR if victory else self.DEFEAT_COLOR
        detail = "You controlled the court." if victory else "The CPU claimed the match."

        title = self.title_font.render(heading, True, heading_color)
        surface.blit(title, title.get_rect(center=(panel.centerx, panel.top + 62)))

        subtitle = self.subtitle_font.render(detail, True, self.theme.text_secondary)
        surface.blit(subtitle, subtitle.get_rect(center=(panel.centerx, panel.top + 105)))

        self._draw_score(surface, panel, result)
        self._draw_actions(surface, panel, actions, selected_index)

        help_text = self.help_font.render(
            "Arrow keys / W-S select  •  Enter confirms  •  Esc returns to menu",
            True,
            self.theme.text_secondary,
        )
        surface.blit(help_text, help_text.get_rect(center=(width // 2, height - 22)))

    def _draw_background(
        self,
        surface: pygame.Surface,
        width: int,
        height: int,
    ) -> None:
        ambience = pygame.Surface((width, height), flags=pygame.SRCALPHA)
        pygame.draw.circle(ambience, (*self.PLAYER_COLOR, 22), (70, height // 2), 260)
        pygame.draw.circle(
            ambience,
            (*self.AI_COLOR, 18),
            (width - 70, height // 2),
            260,
        )
        surface.blit(ambience, (0, 0))

        for x in range(0, width, 48):
            pygame.draw.line(surface, self.GRID_COLOR, (x, 0), (x, height))
        for y in range(0, height, 48):
            pygame.draw.line(surface, self.GRID_COLOR, (0, y), (width, y))

    def _draw_score(
        self,
        surface: pygame.Surface,
        panel: pygame.Rect,
        result: PongResult,
    ) -> None:
        center_y = panel.top + 182
        player_x = panel.centerx - 112
        ai_x = panel.centerx + 112

        player_label = self.label_font.render("PLAYER", True, self.PLAYER_COLOR)
        ai_label = self.label_font.render("CPU", True, self.AI_COLOR)
        divider = self.score_font.render("–", True, self.theme.text_secondary)
        player_score = self.score_font.render(
            str(result.player_score),
            True,
            self.theme.text_primary,
        )
        ai_score = self.score_font.render(
            str(result.ai_score),
            True,
            self.theme.text_primary,
        )

        surface.blit(player_label, player_label.get_rect(center=(player_x, center_y - 38)))
        surface.blit(ai_label, ai_label.get_rect(center=(ai_x, center_y - 38)))
        surface.blit(player_score, player_score.get_rect(center=(player_x, center_y + 12)))
        surface.blit(ai_score, ai_score.get_rect(center=(ai_x, center_y + 12)))
        surface.blit(divider, divider.get_rect(center=(panel.centerx, center_y + 8)))

    def _draw_actions(
        self,
        surface: pygame.Surface,
        panel: pygame.Rect,
        actions: Sequence[tuple[str, str]],
        selected_index: int,
    ) -> None:
        item_width = min(440, panel.width - 70)
        item_height = 48
        spacing = 10
        start_y = panel.bottom - 132

        for index, (label, _) in enumerate(actions):
            rect = pygame.Rect(0, 0, item_width, item_height)
            rect.center = (
                panel.centerx,
                start_y + index * (item_height + spacing),
            )
            selected = index == selected_index

            if selected:
                pygame.draw.rect(surface, (43, 50, 70), rect, border_radius=11)
                pygame.draw.rect(
                    surface,
                    self.theme.accent,
                    rect,
                    width=2,
                    border_radius=11,
                )

            marker = ">" if selected else " "
            color = self.theme.accent if selected else self.theme.text_secondary
            text = self.action_font.render(f"{marker}  {label}", True, color)
            surface.blit(text, text.get_rect(center=rect.center))
