"""Game-specific completed-run presentation for Snake."""

from __future__ import annotations

from collections.abc import Sequence

import pygame

from games.snake.snake_result import SnakeResult
from games.snake.snake_world import GameOverReason, MatchResult
from ui.theme import ArcadeTheme, DEFAULT_THEME


class SnakeResultView:
    """Render immutable Snake results without owning application behavior."""

    BACKGROUND_COLOR = (10, 13, 22)
    SNAKE_COLOR = (93, 193, 112)
    FOOD_COLOR = (239, 94, 103)
    VICTORY_COLOR = (164, 237, 151)
    DEFEAT_COLOR = (239, 112, 123)
    GRID_COLOR = (18, 23, 36)

    def __init__(self, theme: ArcadeTheme = DEFAULT_THEME) -> None:
        self.theme = theme
        self.title_font = pygame.font.Font(None, 68)
        self.subtitle_font = pygame.font.Font(None, 29)
        self.stat_value_font = pygame.font.Font(None, 54)
        self.stat_label_font = pygame.font.Font(None, 20)
        self.action_font = pygame.font.Font(None, 34)
        self.help_font = pygame.font.Font(None, 22)

    def render(
        self,
        surface: pygame.Surface,
        result: object,
        actions: tuple[tuple[str, str], ...],
        selected_index: int,
    ) -> None:
        """Render one completed Snake run and the shared action choices."""
        if not isinstance(result, SnakeResult):
            raise TypeError("SnakeResultView requires a SnakeResult.")

        width, height = surface.get_size()
        surface.fill(self.BACKGROUND_COLOR)
        self._draw_background(surface, width, height)

        panel_width = min(620, max(320, width - 48))
        panel_height = min(440, max(370, height - 54))
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

        victory = result.outcome is MatchResult.WIN
        heading = "GRID MASTERED" if victory else "RUN COMPLETE"
        heading_color = self.VICTORY_COLOR if victory else self.DEFEAT_COLOR
        detail = self._completion_message(result.completion_reason)

        title = self.title_font.render(heading, True, heading_color)
        surface.blit(title, title.get_rect(center=(panel.centerx, panel.top + 58)))

        subtitle = self.subtitle_font.render(detail, True, self.theme.text_secondary)
        surface.blit(subtitle, subtitle.get_rect(center=(panel.centerx, panel.top + 100)))

        self._draw_stats(surface, panel, result)
        self._draw_actions(surface, panel, actions, selected_index)

        help_text = self.help_font.render(
            "Arrow keys / W-S select  •  Enter confirms  •  Esc returns to menu",
            True,
            self.theme.text_secondary,
        )
        surface.blit(help_text, help_text.get_rect(center=(width // 2, height - 22)))

    @staticmethod
    def _completion_message(reason: GameOverReason) -> str:
        messages = {
            GameOverReason.WALL_COLLISION: "The boundary ended the run.",
            GameOverReason.SELF_COLLISION: "The snake crossed its own path.",
            GameOverReason.GRID_COMPLETED: "Every cell belongs to the snake.",
        }
        try:
            return messages[reason]
        except KeyError as error:
            raise ValueError(f"Unsupported Snake completion reason: {reason!r}") from error

    def _draw_background(
        self,
        surface: pygame.Surface,
        width: int,
        height: int,
    ) -> None:
        ambience = pygame.Surface((width, height), flags=pygame.SRCALPHA)
        pygame.draw.circle(
            ambience,
            (*self.SNAKE_COLOR, 20),
            (90, height - 70),
            240,
        )
        pygame.draw.circle(
            ambience,
            (*self.FOOD_COLOR, 15),
            (width - 75, 90),
            205,
        )
        surface.blit(ambience, (0, 0))

        for x in range(0, width, 48):
            pygame.draw.line(surface, self.GRID_COLOR, (x, 0), (x, height))
        for y in range(0, height, 48):
            pygame.draw.line(surface, self.GRID_COLOR, (0, y), (width, y))

    def _draw_stats(
        self,
        surface: pygame.Surface,
        panel: pygame.Rect,
        result: SnakeResult,
    ) -> None:
        stats = (
            ("SCORE", str(result.score), self.SNAKE_COLOR),
            ("SPEED", str(result.speed_level), self.theme.accent),
            ("OUTCOME", "WIN" if result.grid_completed else "LOSS", self.theme.accent_soft),
        )
        spacing = min(155, max(100, (panel.width - 100) // 3))
        total_width = spacing * (len(stats) - 1)
        start_x = panel.centerx - total_width // 2
        center_y = panel.top + 184

        for index, (label, value, accent) in enumerate(stats):
            center_x = start_x + index * spacing
            label_surface = self.stat_label_font.render(label, True, accent)
            value_surface = self.stat_value_font.render(
                value,
                True,
                self.theme.text_primary,
            )
            surface.blit(
                label_surface,
                label_surface.get_rect(center=(center_x, center_y - 29)),
            )
            surface.blit(
                value_surface,
                value_surface.get_rect(center=(center_x, center_y + 12)),
            )

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
