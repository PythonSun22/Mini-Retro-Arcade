"""Snapshot-driven presentation for Snake."""

from __future__ import annotations

import pygame

from games.snake.direction import Direction
from games.snake.snake_world import SnakeSnapshot
from ui.theme import ArcadeTheme, DEFAULT_THEME


class SnakeView:
    """Render Snake without owning simulation, input, or transitions."""

    BACKGROUND_COLOR = (10, 13, 22)
    PLAYFIELD_COLOR = (14, 19, 30)
    PLAYFIELD_BORDER_COLOR = (63, 82, 105)
    GRID_COLOR = (26, 34, 49)

    SNAKE_COLOR = (93, 193, 112)
    SNAKE_INNER_COLOR = (124, 218, 138)
    HEAD_COLOR = (164, 237, 151)
    HEAD_DETAIL_COLOR = (18, 28, 23)

    FOOD_COLOR = (239, 94, 103)
    FOOD_HIGHLIGHT_COLOR = (255, 181, 153)
    FOOD_STEM_COLOR = (103, 197, 119)

    SHADOW_COLOR = (5, 7, 12)

    MIN_MARGIN = 18
    HUD_HEIGHT = 82
    FOOTER_HEIGHT = 62
    PLAYFIELD_PADDING = 12
    PLAYFIELD_BORDER_WIDTH = 2

    def __init__(self, theme: ArcadeTheme = DEFAULT_THEME) -> None:
        self.theme = theme
        self.title_font = pygame.font.Font(None, 34)
        self.value_font = pygame.font.Font(None, 42)
        self.label_font = pygame.font.Font(None, 20)
        self.message_font = pygame.font.Font(None, 28)

    def render(
        self,
        surface: pygame.Surface,
        snapshot: SnakeSnapshot,
    ) -> None:
        """Render one complete Snake frame from immutable snapshot data."""
        width, height = surface.get_size()

        surface.fill(self.BACKGROUND_COLOR)
        self._draw_background(surface, width, height)
        self._draw_hud(surface, snapshot, width)

        playfield_rect, cell_size, origin = self._calculate_playfield(
            surface,
            snapshot,
        )

        self._draw_playfield(
            surface,
            snapshot,
            playfield_rect,
            cell_size,
            origin,
        )
        self._draw_food(surface, snapshot, cell_size, origin)
        self._draw_snake(surface, snapshot, cell_size, origin)

        if snapshot.show_start_prompt:
            self._draw_start_prompt(surface, width, height)

    def _draw_background(
        self,
        surface: pygame.Surface,
        width: int,
        height: int,
    ) -> None:
        """Draw restrained arcade ambience behind the playfield."""
        ambience = pygame.Surface((width, height), flags=pygame.SRCALPHA)

        pygame.draw.circle(
            ambience,
            (*self.SNAKE_COLOR, 16),
            (95, height - 70),
            230,
        )
        pygame.draw.circle(
            ambience,
            (*self.FOOD_COLOR, 12),
            (width - 75, 95),
            190,
        )
        surface.blit(ambience, (0, 0))

        spacing = 48
        background_grid = (18, 23, 36)

        for x in range(0, width, spacing):
            pygame.draw.line(surface, background_grid, (x, 0), (x, height))

        for y in range(0, height, spacing):
            pygame.draw.line(surface, background_grid, (0, y), (width, y))

    def _draw_hud(
        self,
        surface: pygame.Surface,
        snapshot: SnakeSnapshot,
        width: int,
    ) -> None:
        """Draw game title, score, and speed level."""
        title = self.title_font.render("SNAKE", True, self.theme.text_primary)
        surface.blit(title, title.get_rect(center=(width // 2, 27)))

        score_label = self.label_font.render("SCORE", True, self.SNAKE_COLOR)
        score_value = self.value_font.render(
            str(snapshot.score),
            True,
            self.theme.text_primary,
        )
        speed_label = self.label_font.render("SPEED", True, self.theme.accent)
        speed_value = self.value_font.render(
            str(snapshot.speed_level),
            True,
            self.theme.text_primary,
        )

        left_center = width // 2 - 112
        right_center = width // 2 + 112

        surface.blit(score_label, score_label.get_rect(center=(left_center, 26)))
        surface.blit(score_value, score_value.get_rect(center=(left_center, 55)))
        surface.blit(speed_label, speed_label.get_rect(center=(right_center, 26)))
        surface.blit(speed_value, speed_value.get_rect(center=(right_center, 55)))

    def _calculate_playfield(
        self,
        surface: pygame.Surface,
        snapshot: SnakeSnapshot,
    ) -> tuple[pygame.Rect, int, tuple[int, int]]:
        """Return centered responsive playfield geometry."""
        width, height = surface.get_size()

        available_width = max(1, width - self.MIN_MARGIN * 2)
        available_height = max(
            1,
            height
            - self.HUD_HEIGHT
            - self.FOOTER_HEIGHT
            - self.MIN_MARGIN * 2,
        )
        inner_width = max(1, available_width - self.PLAYFIELD_PADDING * 2)
        inner_height = max(1, available_height - self.PLAYFIELD_PADDING * 2)

        cell_size = max(
            1,
            min(
                inner_width // snapshot.grid_width,
                inner_height // snapshot.grid_height,
            ),
        )

        grid_pixel_width = cell_size * snapshot.grid_width
        grid_pixel_height = cell_size * snapshot.grid_height
        playfield_rect = pygame.Rect(
            0,
            0,
            grid_pixel_width + self.PLAYFIELD_PADDING * 2,
            grid_pixel_height + self.PLAYFIELD_PADDING * 2,
        )
        playfield_rect.centerx = width // 2

        content_top = self.HUD_HEIGHT + self.MIN_MARGIN
        content_bottom = height - self.FOOTER_HEIGHT - self.MIN_MARGIN
        playfield_rect.centery = (content_top + content_bottom) // 2

        origin = (
            playfield_rect.left + self.PLAYFIELD_PADDING,
            playfield_rect.top + self.PLAYFIELD_PADDING,
        )
        return playfield_rect, cell_size, origin

    def _draw_playfield(
        self,
        surface: pygame.Surface,
        snapshot: SnakeSnapshot,
        playfield_rect: pygame.Rect,
        cell_size: int,
        origin: tuple[int, int],
    ) -> None:
        """Draw the playfield panel and logical grid."""
        pygame.draw.rect(
            surface,
            self.SHADOW_COLOR,
            playfield_rect.move(0, 7),
            border_radius=14,
        )
        pygame.draw.rect(
            surface,
            self.PLAYFIELD_COLOR,
            playfield_rect,
            border_radius=14,
        )
        pygame.draw.rect(
            surface,
            self.PLAYFIELD_BORDER_COLOR,
            playfield_rect,
            width=self.PLAYFIELD_BORDER_WIDTH,
            border_radius=14,
        )

        origin_x, origin_y = origin
        grid_width = snapshot.grid_width * cell_size
        grid_height = snapshot.grid_height * cell_size

        for x in range(snapshot.grid_width + 1):
            line_x = origin_x + x * cell_size
            pygame.draw.line(
                surface,
                self.GRID_COLOR,
                (line_x, origin_y),
                (line_x, origin_y + grid_height),
            )

        for y in range(snapshot.grid_height + 1):
            line_y = origin_y + y * cell_size
            pygame.draw.line(
                surface,
                self.GRID_COLOR,
                (origin_x, line_y),
                (origin_x + grid_width, line_y),
            )

    def _draw_snake(
        self,
        surface: pygame.Surface,
        snapshot: SnakeSnapshot,
        cell_size: int,
        origin: tuple[int, int],
    ) -> None:
        """Draw the ordered snake body and directional head."""
        for position in reversed(snapshot.snake_body[1:]):
            if not self._is_visible(position, snapshot):
                continue

            rect = self._cell_rect(position, cell_size, origin, inset_ratio=0.13)
            pygame.draw.rect(
                surface,
                self.SNAKE_COLOR,
                rect,
                border_radius=max(2, cell_size // 5),
            )

            inner = rect.inflate(
                -max(2, cell_size // 4),
                -max(2, cell_size // 4),
            )
            if inner.width > 0 and inner.height > 0:
                pygame.draw.rect(
                    surface,
                    self.SNAKE_INNER_COLOR,
                    inner,
                    border_radius=max(1, cell_size // 7),
                )

        if not self._is_visible(snapshot.snake_head, snapshot):
            return

        head_rect = self._cell_rect(
            snapshot.snake_head,
            cell_size,
            origin,
            inset_ratio=0.08,
        )
        pygame.draw.rect(
            surface,
            self.HEAD_COLOR,
            head_rect,
            border_radius=max(3, cell_size // 4),
        )
        self._draw_head_details(
            surface,
            head_rect,
            snapshot.current_direction,
            cell_size,
        )

    def _draw_head_details(
        self,
        surface: pygame.Surface,
        head_rect: pygame.Rect,
        direction: Direction,
        cell_size: int,
    ) -> None:
        """Draw details oriented to the committed direction."""
        eye_radius = max(1, cell_size // 12)
        inset = max(2, cell_size // 4)
        cross_offset = max(2, cell_size // 5)

        if direction is Direction.UP:
            eye_positions = (
                (head_rect.centerx - cross_offset, head_rect.top + inset),
                (head_rect.centerx + cross_offset, head_rect.top + inset),
            )
            nose_start = (head_rect.centerx, head_rect.top + inset)
            nose_end = (head_rect.centerx, head_rect.top + max(1, inset // 3))
        elif direction is Direction.DOWN:
            eye_positions = (
                (head_rect.centerx - cross_offset, head_rect.bottom - inset),
                (head_rect.centerx + cross_offset, head_rect.bottom - inset),
            )
            nose_start = (head_rect.centerx, head_rect.bottom - inset)
            nose_end = (head_rect.centerx, head_rect.bottom - max(1, inset // 3))
        elif direction is Direction.LEFT:
            eye_positions = (
                (head_rect.left + inset, head_rect.centery - cross_offset),
                (head_rect.left + inset, head_rect.centery + cross_offset),
            )
            nose_start = (head_rect.left + inset, head_rect.centery)
            nose_end = (head_rect.left + max(1, inset // 3), head_rect.centery)
        else:
            eye_positions = (
                (head_rect.right - inset, head_rect.centery - cross_offset),
                (head_rect.right - inset, head_rect.centery + cross_offset),
            )
            nose_start = (head_rect.right - inset, head_rect.centery)
            nose_end = (head_rect.right - max(1, inset // 3), head_rect.centery)

        for position in eye_positions:
            pygame.draw.circle(
                surface,
                self.HEAD_DETAIL_COLOR,
                position,
                eye_radius,
            )

        pygame.draw.line(
            surface,
            self.HEAD_DETAIL_COLOR,
            nose_start,
            nose_end,
            width=max(1, cell_size // 12),
        )

    def _draw_food(
        self,
        surface: pygame.Surface,
        snapshot: SnakeSnapshot,
        cell_size: int,
        origin: tuple[int, int],
    ) -> None:
        """Draw food at its logical grid position."""
        position = snapshot.food_position
        if position is None or not self._is_visible(position, snapshot):
            return

        cell_rect = self._cell_rect(position, cell_size, origin, inset_ratio=0.12)
        radius = max(2, min(cell_rect.width, cell_rect.height) // 3)
        center = (
            cell_rect.centerx,
            cell_rect.centery + max(1, cell_size // 14),
        )

        pygame.draw.circle(surface, self.FOOD_COLOR, center, radius)
        pygame.draw.circle(
            surface,
            self.FOOD_HIGHLIGHT_COLOR,
            (
                center[0] - max(1, radius // 3),
                center[1] - max(1, radius // 3),
            ),
            max(1, radius // 3),
        )

        pygame.draw.line(
            surface,
            self.FOOD_STEM_COLOR,
            (center[0], center[1] - radius + max(1, cell_size // 18)),
            (
                center[0] + max(1, cell_size // 8),
                center[1] - radius - max(1, cell_size // 8),
            ),
            width=max(1, cell_size // 10),
        )

    def _draw_start_prompt(
        self,
        surface: pygame.Surface,
        width: int,
        height: int,
    ) -> None:
        """Draw the frontend-owned waiting-state prompt."""
        prompt = self.message_font.render(
            "ARROW KEYS / WASD  —  BEGIN",
            True,
            self.theme.accent,
        )
        prompt_rect = prompt.get_rect(center=(width // 2, height - 34))
        panel_rect = prompt_rect.inflate(34, 16)

        pygame.draw.rect(
            surface,
            self.SHADOW_COLOR,
            panel_rect.move(0, 4),
            border_radius=10,
        )
        pygame.draw.rect(
            surface,
            self.theme.panel,
            panel_rect,
            border_radius=10,
        )
        pygame.draw.rect(
            surface,
            self.theme.panel_border,
            panel_rect,
            width=1,
            border_radius=10,
        )
        surface.blit(prompt, prompt_rect)

    @staticmethod
    def _cell_rect(
        position: tuple[int, int],
        cell_size: int,
        origin: tuple[int, int],
        inset_ratio: float,
    ) -> pygame.Rect:
        """Return a pixel rectangle for one logical grid cell."""
        x, y = position
        origin_x, origin_y = origin
        inset = max(1, int(cell_size * inset_ratio))

        return pygame.Rect(
            origin_x + x * cell_size + inset,
            origin_y + y * cell_size + inset,
            max(1, cell_size - inset * 2),
            max(1, cell_size - inset * 2),
        )

    @staticmethod
    def _is_visible(
        position: tuple[int, int],
        snapshot: SnakeSnapshot,
    ) -> bool:
        """Return whether a logical position lies within the visible grid."""
        x, y = position
        return 0 <= x < snapshot.grid_width and 0 <= y < snapshot.grid_height
