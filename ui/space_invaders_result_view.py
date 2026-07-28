"""Game-specific completed-run presentation for Space Invaders."""

from __future__ import annotations

from collections.abc import Sequence

import pygame

from games.space_invaders.space_invaders_result import SpaceInvadersResult
from games.space_invaders.space_invaders_snapshot import CompletionReason, MatchOutcome
from ui.theme import ArcadeTheme, DEFAULT_THEME


class SpaceInvadersResultView:
    """Render immutable Space Invaders results without owning application behavior."""

    BACKGROUND_COLOR = (8, 11, 20)
    GRID_COLOR = (17, 23, 38)
    PLAYER_COLOR = (106, 205, 255)
    COMMANDER_COLOR = (208, 111, 255)
    SOLDIER_COLOR = (255, 193, 91)
    SCOUT_COLOR = (89, 220, 214)
    VICTORY_COLOR = (164, 237, 151)
    DEFEAT_COLOR = (239, 112, 123)

    def __init__(self, theme: ArcadeTheme = DEFAULT_THEME) -> None:
        self.theme = theme
        self.title_font = pygame.font.Font(None, 66)
        self.subtitle_font = pygame.font.Font(None, 27)
        self.stat_value_font = pygame.font.Font(None, 48)
        self.stat_label_font = pygame.font.Font(None, 18)
        self.action_font = pygame.font.Font(None, 32)
        self.help_font = pygame.font.Font(None, 21)

    def render(
        self,
        surface: pygame.Surface,
        result: object,
        actions: tuple[tuple[str, str], ...],
        selected_index: int,
    ) -> None:
        """Render one completed run and the shared action choices."""
        if not isinstance(result, SpaceInvadersResult):
            raise TypeError("SpaceInvadersResultView requires a SpaceInvadersResult.")

        width, height = surface.get_size()
        surface.fill(self.BACKGROUND_COLOR)
        self._draw_background(surface, width, height)

        panel_width = min(700, max(340, width - 48))
        panel_height = min(460, max(390, height - 42))
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

        victory = result.outcome is MatchOutcome.VICTORY
        heading = "SECTOR SECURED" if victory else "DEFENSE ENDED"
        heading_color = self.VICTORY_COLOR if victory else self.DEFEAT_COLOR

        title = self.title_font.render(heading, True, heading_color)
        surface.blit(title, title.get_rect(center=(panel.centerx, panel.top + 55)))

        subtitle = self.subtitle_font.render(
            self._completion_message(result.completion_reason),
            True,
            self.theme.text_secondary,
        )
        surface.blit(subtitle, subtitle.get_rect(center=(panel.centerx, panel.top + 96)))

        self._draw_stats(surface, panel, result)
        self._draw_actions(surface, panel, actions, selected_index)

        help_text = self.help_font.render(
            "Arrow keys / W-S select  •  Enter confirms  •  Esc returns to menu",
            True,
            self.theme.text_secondary,
        )
        surface.blit(help_text, help_text.get_rect(center=(width // 2, height - 18)))

    @staticmethod
    def _completion_message(reason: CompletionReason) -> str:
        messages = {
            CompletionReason.ALL_WAVES_CLEARED: "Every invasion wave was eliminated.",
            CompletionReason.LIVES_DEPLETED: "The interceptor could no longer hold the line.",
            CompletionReason.INVASION_REACHED_PLAYER: "The formation breached the defense perimeter.",
        }
        try:
            return messages[reason]
        except KeyError as error:
            raise ValueError(
                f"Unsupported Space Invaders completion reason: {reason!r}"
            ) from error

    def _draw_background(
        self,
        surface: pygame.Surface,
        width: int,
        height: int,
    ) -> None:
        ambience = pygame.Surface((width, height), pygame.SRCALPHA)
        pygame.draw.circle(ambience, (*self.PLAYER_COLOR, 18), (85, height - 60), 230)
        pygame.draw.circle(ambience, (*self.COMMANDER_COLOR, 14), (width - 80, 85), 210)
        surface.blit(ambience, (0, 0))

        for x in range(0, width, 48):
            pygame.draw.line(surface, self.GRID_COLOR, (x, 0), (x, height))
        for y in range(0, height, 48):
            pygame.draw.line(surface, self.GRID_COLOR, (0, y), (width, y))

        for index in range(34):
            x = (index * 97 + 19) % max(1, width)
            y = (index * index * 11 + 31) % max(1, height)
            pygame.draw.circle(surface, (112, 139, 181), (x, y), 1)

    def _draw_stats(
        self,
        surface: pygame.Surface,
        panel: pygame.Rect,
        result: SpaceInvadersResult,
    ) -> None:
        stats = (
            ("FINAL SCORE", str(result.score), self.PLAYER_COLOR),
            ("WAVES", str(result.waves_completed), self.SOLDIER_COLOR),
            ("ENEMIES", str(result.enemies_destroyed), self.SCOUT_COLOR),
            ("LIVES", str(result.remaining_lives), self.COMMANDER_COLOR),
        )
        spacing = min(145, max(78, (panel.width - 90) // 4))
        total_width = spacing * (len(stats) - 1)
        start_x = panel.centerx - total_width // 2
        center_y = panel.top + 178

        for index, (label, value, accent) in enumerate(stats):
            center_x = start_x + index * spacing
            label_surface = self.stat_label_font.render(label, True, accent)
            value_surface = self.stat_value_font.render(value, True, self.theme.text_primary)
            surface.blit(label_surface, label_surface.get_rect(center=(center_x, center_y - 27)))
            surface.blit(value_surface, value_surface.get_rect(center=(center_x, center_y + 10)))

    def _draw_actions(
        self,
        surface: pygame.Surface,
        panel: pygame.Rect,
        actions: Sequence[tuple[str, str]],
        selected_index: int,
    ) -> None:
        item_width = min(460, panel.width - 70)
        item_height = 48
        spacing = 10
        start_y = panel.bottom - 130

        for index, (label, _) in enumerate(actions):
            rect = pygame.Rect(0, 0, item_width, item_height)
            rect.center = (panel.centerx, start_y + index * (item_height + spacing))
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
