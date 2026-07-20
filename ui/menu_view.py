"""Reusable keyboard-menu presentation components."""

from __future__ import annotations

from collections.abc import Sequence

import pygame

from ui.theme import ArcadeTheme, DEFAULT_THEME


class MenuView:
    """Draw a centered arcade menu without owning input or navigation logic."""

    def __init__(
        self,
        title: str,
        subtitle: str,
        help_text: str,
        theme: ArcadeTheme = DEFAULT_THEME,
    ) -> None:
        self.title = title
        self.subtitle = subtitle
        self.help_text = help_text
        self.theme = theme

        self.title_font = pygame.font.Font(None, 76)
        self.subtitle_font = pygame.font.Font(None, 28)
        self.item_font = pygame.font.Font(None, 38)
        self.help_font = pygame.font.Font(None, 24)

    def render(
        self,
        surface: pygame.Surface,
        labels: Sequence[str],
        selected_index: int,
    ) -> None:
        """Render menu content onto the shared application surface."""
        surface.fill(self.theme.background)
        width, height = surface.get_size()

        self._draw_background(surface, width, height)
        self._draw_header(surface, width)
        self._draw_menu_panel(surface, width, height, labels, selected_index)
        self._draw_help(surface, width, height)

    def _draw_background(
        self,
        surface: pygame.Surface,
        width: int,
        height: int,
    ) -> None:
        pygame.draw.circle(
            surface,
            (19, 37, 58),
            (width - 90, 70),
            190,
        )
        pygame.draw.circle(
            surface,
            (35, 25, 52),
            (80, height - 35),
            220,
        )

        for x in range(0, width, 48):
            pygame.draw.line(
                surface,
                (19, 23, 36),
                (x, 0),
                (x, height),
                1,
            )

    def _draw_header(self, surface: pygame.Surface, width: int) -> None:
        title = self.title_font.render(
            self.title,
            True,
            self.theme.text_primary,
        )
        surface.blit(title, title.get_rect(center=(width // 2, 88)))

        subtitle = self.subtitle_font.render(
            self.subtitle,
            True,
            self.theme.accent_soft,
        )
        surface.blit(subtitle, subtitle.get_rect(center=(width // 2, 132)))

    def _draw_menu_panel(
        self,
        surface: pygame.Surface,
        width: int,
        height: int,
        labels: Sequence[str],
        selected_index: int,
    ) -> None:
        panel_width = min(500, width - self.theme.outer_margin * 2)
        content_height = (
            len(labels) * self.theme.item_height
            + max(0, len(labels) - 1) * self.theme.item_spacing
        )
        panel_height = content_height + 62
        panel_rect = pygame.Rect(0, 0, panel_width, panel_height)
        panel_rect.center = (width // 2, height // 2 + 36)

        shadow_rect = panel_rect.move(0, 9)
        pygame.draw.rect(
            surface,
            self.theme.shadow,
            shadow_rect,
            border_radius=self.theme.panel_radius,
        )
        pygame.draw.rect(
            surface,
            self.theme.panel,
            panel_rect,
            border_radius=self.theme.panel_radius,
        )
        pygame.draw.rect(
            surface,
            self.theme.panel_border,
            panel_rect,
            width=2,
            border_radius=self.theme.panel_radius,
        )

        item_y = panel_rect.top + 31
        item_rect = pygame.Rect(
            panel_rect.left + 24,
            item_y,
            panel_rect.width - 48,
            self.theme.item_height,
        )

        for index, label in enumerate(labels):
            selected = index == selected_index
            self._draw_menu_item(surface, item_rect, label, selected)
            item_rect.y += self.theme.item_height + self.theme.item_spacing

    def _draw_menu_item(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        label: str,
        selected: bool,
    ) -> None:
        if selected:
            pygame.draw.rect(
                surface,
                (43, 50, 70),
                rect,
                border_radius=12,
            )
            pygame.draw.rect(
                surface,
                self.theme.accent,
                rect,
                width=2,
                border_radius=12,
            )

        marker = ">" if selected else " "
        color = self.theme.accent if selected else self.theme.text_secondary
        text = self.item_font.render(f"{marker}  {label}", True, color)
        surface.blit(text, text.get_rect(midleft=(rect.left + 22, rect.centery)))

    def _draw_help(
        self,
        surface: pygame.Surface,
        width: int,
        height: int,
    ) -> None:
        help_surface = self.help_font.render(
            self.help_text,
            True,
            self.theme.text_secondary,
        )
        surface.blit(
            help_surface,
            help_surface.get_rect(center=(width // 2, height - 32)),
        )
