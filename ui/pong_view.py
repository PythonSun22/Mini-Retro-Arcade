"""Snapshot-driven presentation for Pong."""

from __future__ import annotations

import pygame

from games.pong.pong_world import PongSnapshot
from ui.theme import ArcadeTheme, DEFAULT_THEME


class PongView:
    """Render Pong without owning simulation, input, or transitions."""

    BACKGROUND_COLOR = (10, 13, 22)
    COURT_COLOR = (15, 20, 32)
    COURT_BORDER_COLOR = (67, 82, 112)
    COURT_MARKING_COLOR = (74, 87, 113)

    PLAYER_COLOR = (106, 205, 255)
    AI_COLOR = (255, 211, 92)
    BALL_COLOR = (241, 244, 255)

    SHADOW_COLOR = (5, 7, 12)
    MUTED_COLOR = (145, 150, 165)

    COURT_MARGIN_X = 20
    COURT_MARGIN_Y = 18
    COURT_BORDER_WIDTH = 2

    HIT_FLASH_COLOR = (255, 255, 255)
    HIT_FLASH_DURATION_MS = 140

    def __init__(
        self,
        theme: ArcadeTheme = DEFAULT_THEME,
    ) -> None:
        self.theme = theme

        self.score_font = pygame.font.Font(None, 64)
        self.label_font = pygame.font.Font(None, 22)
        self.message_font = pygame.font.Font(None, 30)

        self._previous_ball_x: float | None = None
        self._previous_ball_direction = 0

        self._player_flash_until = 0
        self._ai_flash_until = 0

    def render(
        self,
        surface: pygame.Surface,
        snapshot: PongSnapshot,
    ) -> None:
        """Render one complete Pong frame from immutable snapshot data."""
        width, height = surface.get_size()

        surface.fill(self.BACKGROUND_COLOR)

        self._draw_background(surface, width, height)
        self._draw_court(surface, width, height)
        self._draw_entities(surface, snapshot)
        self._draw_hud(surface, snapshot, width)

        if snapshot.show_serve_prompt:
            self._draw_serve_prompt(surface, width, height)

    def _draw_background(
        self,
        surface: pygame.Surface,
        width: int,
        height: int,
    ) -> None:
        """Draw restrained arcade ambience behind the court."""
        ambience = pygame.Surface(
            (width, height),
            flags=pygame.SRCALPHA,
        )

        pygame.draw.circle(
            ambience,
            (*self.PLAYER_COLOR, 18),
            (80, height // 2),
            250,
        )

        pygame.draw.circle(
            ambience,
            (*self.AI_COLOR, 14),
            (width - 80, height // 2),
            250,
        )

        surface.blit(ambience, (0, 0))

        grid_spacing = 48
        grid_color = (19, 24, 38)

        for x in range(0, width, grid_spacing):
            pygame.draw.line(
                surface,
                grid_color,
                (x, 0),
                (x, height),
            )

        for y in range(0, height, grid_spacing):
            pygame.draw.line(
                surface,
                grid_color,
                (0, y),
                (width, y),
            )

    def _draw_court(
        self,
        surface: pygame.Surface,
        width: int,
        height: int,
    ) -> None:
        """Draw the court surface and permanent markings."""
        court_rect = pygame.Rect(
            self.COURT_MARGIN_X,
            self.COURT_MARGIN_Y,
            width - self.COURT_MARGIN_X * 2,
            height - self.COURT_MARGIN_Y * 2,
        )

        shadow_rect = court_rect.move(0, 6)

        pygame.draw.rect(
            surface,
            self.SHADOW_COLOR,
            shadow_rect,
            border_radius=12,
        )

        pygame.draw.rect(
            surface,
            self.COURT_COLOR,
            court_rect,
            border_radius=12,
        )

        pygame.draw.rect(
            surface,
            self.COURT_BORDER_COLOR,
            court_rect,
            width=self.COURT_BORDER_WIDTH,
            border_radius=12,
        )

        self._draw_center_circle(surface, width, height)
        self._draw_center_line(surface, width, height)

    def _draw_center_circle(
        self,
        surface: pygame.Surface,
        width: int,
        height: int,
    ) -> None:
        pygame.draw.circle(
            surface,
            self.COURT_MARKING_COLOR,
            (width // 2, height // 2),
            58,
            width=2,
        )

        pygame.draw.circle(
            surface,
            self.COURT_MARKING_COLOR,
            (width // 2, height // 2),
            5,
        )

    def _draw_center_line(
        self,
        surface: pygame.Surface,
        width: int,
        height: int,
    ) -> None:
        segment_height = 18
        gap = 14
        x = width // 2 - 2

        start_y = self.COURT_MARGIN_Y + 10
        end_y = height - self.COURT_MARGIN_Y - 10

        for y in range(start_y, end_y, segment_height + gap):
            visible_height = min(segment_height, end_y - y)

            pygame.draw.rect(
                surface,
                self.COURT_MARKING_COLOR,
                pygame.Rect(x, y, 4, visible_height),
                border_radius=2,
            )

    def _draw_entities(
        self,
        surface: pygame.Surface,
        snapshot: PongSnapshot,
    ) -> None:
        """Draw entities with lightweight paddle-contact feedback."""
        player_rect = pygame.Rect(snapshot.player_paddle_bounds)
        ai_rect = pygame.Rect(snapshot.ai_paddle_bounds)
        ball_rect = pygame.Rect(snapshot.ball_bounds)

        self._update_hit_feedback(snapshot)

        current_time = pygame.time.get_ticks()

        player_color = (
            self.HIT_FLASH_COLOR
            if current_time < self._player_flash_until
            else self.PLAYER_COLOR
        )

        ai_color = (
            self.HIT_FLASH_COLOR
            if current_time < self._ai_flash_until
            else self.AI_COLOR
        )

        self._draw_paddle(surface, player_rect, player_color)
        self._draw_paddle(surface, ai_rect, ai_color)
        self._draw_ball(surface, ball_rect)

    def _update_hit_feedback(
        self,
        snapshot: PongSnapshot,
    ) -> None:
        """Flash the appropriate paddle when the ball reverses direction."""
        ball_x = snapshot.ball_position[0]

        if self._previous_ball_x is None:
            self._previous_ball_x = ball_x
            return

        movement_x = ball_x - self._previous_ball_x

        if movement_x > 0.0:
            current_direction = 1
        elif movement_x < 0.0:
            current_direction = -1
        else:
            current_direction = 0

        current_time = pygame.time.get_ticks()

        if (
            self._previous_ball_direction < 0
            and current_direction > 0
        ):
            self._player_flash_until = (
                current_time + self.HIT_FLASH_DURATION_MS
            )

        elif (
            self._previous_ball_direction > 0
            and current_direction < 0
        ):
            self._ai_flash_until = (
                current_time + self.HIT_FLASH_DURATION_MS
            )

        if current_direction != 0:
            self._previous_ball_direction = current_direction

        self._previous_ball_x = ball_x

    def _draw_paddle(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        color: tuple[int, int, int],
    ) -> None:
        pygame.draw.rect(
            surface,
            color,
            rect,
            border_radius=5,
        )

        highlight_rect = pygame.Rect(
            rect.left + 3,
            rect.top + 4,
            max(2, rect.width // 4),
            max(4, rect.height - 8),
        )

        pygame.draw.rect(
            surface,
            self.theme.text_primary,
            highlight_rect,
            border_radius=3,
        )

    def _draw_ball(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
    ) -> None:
        pygame.draw.rect(
            surface,
            self.BALL_COLOR,
            rect,
            border_radius=5,
        )

        highlight_size = max(3, rect.width // 4)

        pygame.draw.rect(
            surface,
            (255, 255, 255),
            pygame.Rect(
                rect.left + 3,
                rect.top + 3,
                highlight_size,
                highlight_size,
            ),
            border_radius=2,
        )

    def _draw_hud(
        self,
        surface: pygame.Surface,
        snapshot: PongSnapshot,
        width: int,
    ) -> None:
        """Draw player labels, scores, and the match target."""
        player_center_x = width // 2 - 100
        ai_center_x = width // 2 + 100

        player_label = self.label_font.render(
            "PLAYER",
            True,
            self.PLAYER_COLOR,
        )

        ai_label = self.label_font.render(
            "CPU",
            True,
            self.AI_COLOR,
        )

        player_score = self.score_font.render(
            str(snapshot.player_score),
            True,
            self.theme.text_primary,
        )

        ai_score = self.score_font.render(
            str(snapshot.ai_score),
            True,
            self.theme.text_primary,
        )

        target_text = self.label_font.render(
            f"FIRST TO {snapshot.winning_score}",
            True,
            self.MUTED_COLOR,
        )

        surface.blit(
            player_label,
            player_label.get_rect(center=(player_center_x, 35)),
        )

        surface.blit(
            ai_label,
            ai_label.get_rect(center=(ai_center_x, 35)),
        )

        surface.blit(
            player_score,
            player_score.get_rect(center=(player_center_x, 72)),
        )

        surface.blit(
            ai_score,
            ai_score.get_rect(center=(ai_center_x, 72)),
        )

        surface.blit(
            target_text,
            target_text.get_rect(center=(width // 2, 33)),
        )

    def _draw_serve_prompt(
        self,
        surface: pygame.Surface,
        width: int,
        height: int,
    ) -> None:
        prompt_text = "SPACE / ENTER  —  SERVE"

        prompt = self.message_font.render(
            prompt_text,
            True,
            self.theme.accent,
        )

        prompt_rect = prompt.get_rect(
            center=(width // 2, height - 48),
        )

        panel_rect = prompt_rect.inflate(38, 18)

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