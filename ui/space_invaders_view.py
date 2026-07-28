"""Snapshot-driven presentation for Space Invaders."""

from __future__ import annotations

import math

import pygame

from games.space_invaders.enemy import EnemyKind
from games.space_invaders.projectile import ProjectileOwner
from games.space_invaders.space_invaders_snapshot import (
    EnemySnapshot,
    PlayerSnapshot,
    ProjectileSnapshot,
    SpaceInvadersSnapshot,
)
from ui.theme import ArcadeTheme, DEFAULT_THEME


class SpaceInvadersView:
    """Render Space Invaders without owning simulation, input, or transitions."""

    BACKGROUND_COLOR = (8, 11, 20)
    PLAYFIELD_COLOR = (12, 17, 29)
    PLAYFIELD_BORDER_COLOR = (58, 75, 104)
    GRID_COLOR = (18, 25, 40)
    STAR_COLOR = (126, 151, 190)

    PLAYER_COLOR = (222, 238, 255)
    PLAYER_ACCENT = (106, 205, 255)
    PLAYER_CORE = (245, 250, 255)

    COMMANDER_COLOR = (208, 111, 255)
    SOLDIER_COLOR = (255, 193, 91)
    SCOUT_COLOR = (89, 220, 214)
    ENEMY_EYE_COLOR = (247, 250, 255)

    PLAYER_PROJECTILE_COLOR = (151, 224, 255)
    ENEMY_PROJECTILE_COLOR = (255, 104, 153)
    SHADOW_COLOR = (4, 6, 11)

    HUD_HEIGHT = 76
    FOOTER_HEIGHT = 42
    MIN_MARGIN = 16
    PLAYFIELD_PADDING = 10

    def __init__(self, theme: ArcadeTheme = DEFAULT_THEME) -> None:
        self.theme = theme
        self.title_font = pygame.font.Font(None, 34)
        self.value_font = pygame.font.Font(None, 38)
        self.label_font = pygame.font.Font(None, 19)
        self.message_font = pygame.font.Font(None, 27)

        self._previous_enemy_ids: frozenset[int] | None = None
        self._enemy_flash_until: dict[int, int] = {}
        self._previous_score = 0
        self._score_flash_until = 0
        self._previous_wave = 1
        self._wave_flash_until = 0

    def render(
        self,
        surface: pygame.Surface,
        snapshot: SpaceInvadersSnapshot,
    ) -> None:
        """Render one complete frame from immutable snapshot data."""
        if snapshot.version != 1:
            raise ValueError(
                f"SpaceInvadersView supports snapshot version 1, got {snapshot.version}."
            )

        width, height = surface.get_size()
        now = pygame.time.get_ticks()
        self._track_visual_changes(snapshot, now)

        surface.fill(self.BACKGROUND_COLOR)
        self._draw_background(surface, width, height)
        self._draw_hud(surface, snapshot, width, now)

        playfield, scale, origin = self._calculate_playfield(surface, snapshot)
        self._draw_playfield(surface, playfield)

        glow_layer = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        self._draw_enemy_glows(glow_layer, snapshot, scale, origin, now)
        self._draw_projectile_glows(glow_layer, snapshot, scale, origin)
        self._draw_player_glow(glow_layer, snapshot.player, scale, origin)
        surface.blit(glow_layer, (0, 0))

        for enemy in snapshot.enemies:
            self._draw_enemy(surface, enemy, scale, origin, now)
        for projectile in snapshot.projectiles:
            self._draw_projectile(surface, projectile, scale, origin)
        self._draw_player(surface, snapshot.player, scale, origin, now)

        if snapshot.show_start_prompt:
            self._draw_start_prompt(surface, width, height)

    def _track_visual_changes(
        self,
        snapshot: SpaceInvadersSnapshot,
        now: int,
    ) -> None:
        current_ids = frozenset(enemy.enemy_id for enemy in snapshot.enemies)
        if self._previous_enemy_ids is not None:
            for enemy_id in self._previous_enemy_ids - current_ids:
                self._enemy_flash_until[enemy_id] = now + 150
        self._previous_enemy_ids = current_ids

        if snapshot.score > self._previous_score:
            self._score_flash_until = now + 180
        self._previous_score = snapshot.score

        if snapshot.wave != self._previous_wave:
            self._wave_flash_until = now + 650
        self._previous_wave = snapshot.wave

        self._enemy_flash_until = {
            enemy_id: deadline
            for enemy_id, deadline in self._enemy_flash_until.items()
            if deadline > now
        }

    def _draw_background(
        self,
        surface: pygame.Surface,
        width: int,
        height: int,
    ) -> None:
        ambience = pygame.Surface((width, height), pygame.SRCALPHA)
        pygame.draw.circle(
            ambience,
            (*self.PLAYER_ACCENT, 16),
            (width // 2, height + 30),
            min(width, height) // 2,
        )
        pygame.draw.circle(
            ambience,
            (*self.COMMANDER_COLOR, 10),
            (width - 80, 90),
            220,
        )
        surface.blit(ambience, (0, 0))

        for x in range(0, width, 48):
            pygame.draw.line(surface, self.GRID_COLOR, (x, 0), (x, height))
        for y in range(0, height, 48):
            pygame.draw.line(surface, self.GRID_COLOR, (0, y), (width, y))

        # Fixed deterministic stars avoid gameplay-side or frame-side randomness.
        for index in range(46):
            x = (index * 83 + 37) % max(1, width)
            y = (index * index * 17 + index * 29 + 41) % max(1, height)
            radius = 1 if index % 5 else 2
            pygame.draw.circle(surface, self.STAR_COLOR, (x, y), radius)

    def _draw_hud(
        self,
        surface: pygame.Surface,
        snapshot: SpaceInvadersSnapshot,
        width: int,
        now: int,
    ) -> None:
        """Draw one balanced HUD row beneath the centered game title."""
        title = self.title_font.render(
            "SPACE INVADERS",
            True,
            self.theme.text_primary,
        )
        surface.blit(title, title.get_rect(center=(width // 2, 18)))

        row_y = 52
        score_color = (
            self.theme.accent
            if now < self._score_flash_until
            else self.PLAYER_ACCENT
        )

        score_text = self.message_font.render(
            f"SCORE  {snapshot.score}",
            True,
            score_color,
        )
        wave_text = self.message_font.render(
            f"WAVE  {snapshot.wave}",
            True,
            self.SOLDIER_COLOR,
        )
        lives_label = self.message_font.render(
            "LIVES",
            True,
            self.PLAYER_ACCENT,
        )

        left_anchor = max(self.MIN_MARGIN + 14, width // 2 - 270)
        right_anchor = min(width - self.MIN_MARGIN - 14, width // 2 + 270)

        surface.blit(score_text, score_text.get_rect(midleft=(left_anchor, row_y)))
        surface.blit(wave_text, wave_text.get_rect(center=(width // 2, row_y)))

        heart_spacing = 19
        heart_size = 11
        heart_total_width = max(0, snapshot.player.lives * heart_spacing - 5)
        group_width = lives_label.get_width() + 13 + heart_total_width
        group_left = right_anchor - group_width
        surface.blit(
            lives_label,
            lives_label.get_rect(midleft=(group_left, row_y)),
        )

        heart_x = group_left + lives_label.get_width() + 13
        for life_index in range(snapshot.player.lives):
            self._draw_hud_heart(
                surface,
                (heart_x + life_index * heart_spacing, row_y),
                heart_size,
            )

        if now < self._wave_flash_until:
            banner = self.message_font.render(
                f"WAVE {snapshot.wave}",
                True,
                self.theme.accent,
            )
            surface.blit(
                banner,
                banner.get_rect(center=(width // 2, self.HUD_HEIGHT + 20)),
            )

    def _draw_hud_heart(
        self,
        surface: pygame.Surface,
        center: tuple[int, int],
        size: int,
    ) -> None:
        """Draw a small procedural life heart without relying on font glyphs."""
        x, y = center
        radius = max(2, size // 3)
        color = self.PLAYER_ACCENT
        pygame.draw.circle(surface, color, (x - radius, y - radius // 2), radius)
        pygame.draw.circle(surface, color, (x + radius, y - radius // 2), radius)
        pygame.draw.polygon(
            surface,
            color,
            (
                (x - radius * 2, y),
                (x + radius * 2, y),
                (x, y + size),
            ),
        )

    def _calculate_playfield(
        self,
        surface: pygame.Surface,
        snapshot: SpaceInvadersSnapshot,
    ) -> tuple[pygame.Rect, float, tuple[float, float]]:
        width, height = surface.get_size()
        available_width = max(1, width - self.MIN_MARGIN * 2)
        available_height = max(
            1,
            height - self.HUD_HEIGHT - self.FOOTER_HEIGHT - self.MIN_MARGIN * 2,
        )
        inner_width = max(1, available_width - self.PLAYFIELD_PADDING * 2)
        inner_height = max(1, available_height - self.PLAYFIELD_PADDING * 2)

        scale = min(
            inner_width / snapshot.world_width,
            inner_height / snapshot.world_height,
        )
        world_pixel_width = max(1, round(snapshot.world_width * scale))
        world_pixel_height = max(1, round(snapshot.world_height * scale))

        playfield = pygame.Rect(
            0,
            0,
            world_pixel_width + self.PLAYFIELD_PADDING * 2,
            world_pixel_height + self.PLAYFIELD_PADDING * 2,
        )
        playfield.centerx = width // 2
        content_top = self.HUD_HEIGHT + self.MIN_MARGIN
        content_bottom = height - self.FOOTER_HEIGHT - self.MIN_MARGIN
        playfield.centery = (content_top + content_bottom) // 2

        origin = (
            float(playfield.left + self.PLAYFIELD_PADDING),
            float(playfield.top + self.PLAYFIELD_PADDING),
        )
        return playfield, scale, origin

    def _draw_playfield(self, surface: pygame.Surface, rect: pygame.Rect) -> None:
        pygame.draw.rect(
            surface,
            self.SHADOW_COLOR,
            rect.move(0, 6),
            border_radius=14,
        )
        pygame.draw.rect(surface, self.PLAYFIELD_COLOR, rect, border_radius=14)
        pygame.draw.rect(
            surface,
            self.PLAYFIELD_BORDER_COLOR,
            rect,
            width=2,
            border_radius=14,
        )

    @staticmethod
    def _screen_rect(
        x: float,
        y: float,
        width: float,
        height: float,
        scale: float,
        origin: tuple[float, float],
    ) -> pygame.Rect:
        return pygame.Rect(
            round(origin[0] + x * scale),
            round(origin[1] + y * scale),
            max(2, round(width * scale)),
            max(2, round(height * scale)),
        )

    @classmethod
    def _enemy_color(cls, kind: EnemyKind) -> tuple[int, int, int]:
        colors = {
            EnemyKind.COMMANDER: cls.COMMANDER_COLOR,
            EnemyKind.SOLDIER: cls.SOLDIER_COLOR,
            EnemyKind.SCOUT: cls.SCOUT_COLOR,
        }
        try:
            return colors[kind]
        except KeyError as error:
            raise ValueError(f"Unsupported enemy kind: {kind!r}") from error

    def _draw_enemy_glows(
        self,
        layer: pygame.Surface,
        snapshot: SpaceInvadersSnapshot,
        scale: float,
        origin: tuple[float, float],
        now: int,
    ) -> None:
        for enemy in snapshot.enemies:
            rect = self._screen_rect(
                enemy.x,
                enemy.y,
                enemy.width,
                enemy.height,
                scale,
                origin,
            )
            color = self._enemy_color(enemy.kind)
            alpha = 62 if now < self._enemy_flash_until.get(enemy.enemy_id, 0) else 28
            pygame.draw.ellipse(layer, (*color, alpha), rect.inflate(14, 10))

    def _draw_projectile_glows(
        self,
        layer: pygame.Surface,
        snapshot: SpaceInvadersSnapshot,
        scale: float,
        origin: tuple[float, float],
    ) -> None:
        for projectile in snapshot.projectiles:
            rect = self._screen_rect(
                projectile.x,
                projectile.y,
                projectile.width,
                projectile.height,
                scale,
                origin,
            )
            color = (
                self.PLAYER_PROJECTILE_COLOR
                if projectile.owner is ProjectileOwner.PLAYER
                else self.ENEMY_PROJECTILE_COLOR
            )
            pygame.draw.ellipse(layer, (*color, 70), rect.inflate(10, 10))

    def _draw_player_glow(
        self,
        layer: pygame.Surface,
        player: PlayerSnapshot,
        scale: float,
        origin: tuple[float, float],
    ) -> None:
        rect = self._screen_rect(player.x, player.y, player.width, player.height, scale, origin)
        alpha = 54 if player.invulnerable else 30
        pygame.draw.ellipse(layer, (*self.PLAYER_ACCENT, alpha), rect.inflate(18, 14))

    def _draw_player(
        self,
        surface: pygame.Surface,
        player: PlayerSnapshot,
        scale: float,
        origin: tuple[float, float],
        now: int,
    ) -> None:
        rect = self._screen_rect(player.x, player.y, player.width, player.height, scale, origin)
        if player.invulnerable and (now // 90) % 2 == 0:
            return

        cx, cy = rect.center
        left, right, top, bottom = rect.left, rect.right, rect.top, rect.bottom
        wing_y = top + max(2, rect.height // 2)
        hull = [
            (cx, top),
            (cx + max(2, rect.width // 7), wing_y),
            (right, bottom - max(1, rect.height // 5)),
            (right - max(2, rect.width // 5), bottom),
            (cx, bottom - max(1, rect.height // 5)),
            (left + max(2, rect.width // 5), bottom),
            (left, bottom - max(1, rect.height // 5)),
            (cx - max(2, rect.width // 7), wing_y),
        ]
        pygame.draw.polygon(surface, self.PLAYER_COLOR, hull)
        pygame.draw.polygon(surface, self.PLAYER_ACCENT, hull, width=max(1, rect.width // 18))

        core_radius = max(2, min(rect.width, rect.height) // 7)
        pygame.draw.circle(surface, self.PLAYER_ACCENT, (cx, wing_y), core_radius + 1)
        pygame.draw.circle(surface, self.PLAYER_CORE, (cx, wing_y), core_radius)
        pygame.draw.line(
            surface,
            self.PLAYER_CORE,
            (cx, top + 1),
            (cx, wing_y - core_radius),
            width=max(1, rect.width // 20),
        )

        if player.invulnerable:
            pulse = 2 + int(2 * (0.5 + 0.5 * math.sin(now / 80.0)))
            pygame.draw.ellipse(
                surface,
                self.PLAYER_ACCENT,
                rect.inflate(pulse * 4, pulse * 3),
                width=max(1, pulse // 2),
            )

    def _draw_enemy(
        self,
        surface: pygame.Surface,
        enemy: EnemySnapshot,
        scale: float,
        origin: tuple[float, float],
        now: int,
    ) -> None:
        rect = self._screen_rect(enemy.x, enemy.y, enemy.width, enemy.height, scale, origin)
        color = self._enemy_color(enemy.kind)
        flash = now < self._enemy_flash_until.get(enemy.enemy_id, 0)
        hull_color = self.ENEMY_EYE_COLOR if flash else color

        if enemy.kind is EnemyKind.COMMANDER:
            self._draw_commander(surface, rect, hull_color)
        elif enemy.kind is EnemyKind.SOLDIER:
            self._draw_soldier(surface, rect, hull_color)
        elif enemy.kind is EnemyKind.SCOUT:
            self._draw_scout(surface, rect, hull_color)
        else:
            raise ValueError(f"Unsupported enemy kind: {enemy.kind!r}")

    def _draw_commander(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        color: tuple[int, int, int],
    ) -> None:
        cx = rect.centerx
        points = [
            (rect.left, rect.centery),
            (rect.left + rect.width // 5, rect.top + rect.height // 5),
            (cx - rect.width // 8, rect.top + rect.height // 5),
            (cx, rect.top),
            (cx + rect.width // 8, rect.top + rect.height // 5),
            (rect.right - rect.width // 5, rect.top + rect.height // 5),
            (rect.right, rect.centery),
            (rect.right - rect.width // 6, rect.bottom),
            (rect.left + rect.width // 6, rect.bottom),
        ]
        pygame.draw.polygon(surface, color, points)
        pygame.draw.polygon(surface, self.COMMANDER_COLOR, points, width=max(1, rect.width // 14))
        for offset in (-rect.width // 5, 0, rect.width // 5):
            pygame.draw.circle(
                surface,
                self.ENEMY_EYE_COLOR,
                (cx + offset, rect.centery),
                max(1, rect.height // 8),
            )

    def _draw_soldier(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        color: tuple[int, int, int],
    ) -> None:
        points = [
            (rect.left + rect.width // 5, rect.top),
            (rect.right - rect.width // 5, rect.top),
            (rect.right, rect.centery),
            (rect.right - rect.width // 6, rect.bottom),
            (rect.centerx, rect.bottom - rect.height // 5),
            (rect.left + rect.width // 6, rect.bottom),
            (rect.left, rect.centery),
        ]
        pygame.draw.polygon(surface, color, points)
        pygame.draw.polygon(surface, self.SOLDIER_COLOR, points, width=max(1, rect.width // 15))
        eye_y = rect.top + rect.height // 2
        for eye_x in (rect.left + rect.width // 3, rect.right - rect.width // 3):
            pygame.draw.circle(surface, self.ENEMY_EYE_COLOR, (eye_x, eye_y), max(1, rect.height // 9))

    def _draw_scout(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        color: tuple[int, int, int],
    ) -> None:
        points = [
            (rect.left, rect.centery),
            (rect.centerx - rect.width // 7, rect.top),
            (rect.centerx, rect.top + rect.height // 4),
            (rect.centerx + rect.width // 7, rect.top),
            (rect.right, rect.centery),
            (rect.centerx, rect.bottom),
        ]
        pygame.draw.polygon(surface, color, points)
        pygame.draw.polygon(surface, self.SCOUT_COLOR, points, width=max(1, rect.width // 15))
        pygame.draw.circle(
            surface,
            self.ENEMY_EYE_COLOR,
            rect.center,
            max(1, rect.height // 8),
        )

    def _draw_projectile(
        self,
        surface: pygame.Surface,
        projectile: ProjectileSnapshot,
        scale: float,
        origin: tuple[float, float],
    ) -> None:
        rect = self._screen_rect(
            projectile.x,
            projectile.y,
            projectile.width,
            projectile.height,
            scale,
            origin,
        )
        rect.width = max(rect.width, 3)

        if projectile.owner is ProjectileOwner.PLAYER:
            pygame.draw.rect(
                surface,
                self.PLAYER_PROJECTILE_COLOR,
                rect,
                border_radius=max(1, rect.width // 2),
            )
            pygame.draw.line(
                surface,
                self.PLAYER_CORE,
                (rect.centerx, rect.top),
                (rect.centerx, rect.bottom),
                width=1,
            )
        elif projectile.owner is ProjectileOwner.ENEMY:
            radius = max(2, rect.width)
            pygame.draw.circle(surface, self.ENEMY_PROJECTILE_COLOR, (rect.centerx, rect.top + radius), radius)
            pygame.draw.line(
                surface,
                self.ENEMY_PROJECTILE_COLOR,
                (rect.centerx, rect.top + radius * 2),
                (rect.centerx, rect.bottom),
                width=max(1, rect.width // 2),
            )
            pygame.draw.circle(surface, self.theme.accent, (rect.centerx, rect.top + radius), max(1, radius // 2))
        else:
            raise ValueError(f"Unsupported projectile owner: {projectile.owner!r}")

    def _draw_start_prompt(
        self,
        surface: pygame.Surface,
        width: int,
        height: int,
    ) -> None:
        prompt = self.message_font.render(
            "ARROWS / A-D MOVE   •   SPACE FIRES",
            True,
            self.theme.accent,
        )
        prompt_rect = prompt.get_rect(center=(width // 2, height - 24))
        panel = prompt_rect.inflate(34, 14)
        pygame.draw.rect(surface, self.SHADOW_COLOR, panel.move(0, 4), border_radius=10)
        pygame.draw.rect(surface, self.theme.panel, panel, border_radius=10)
        pygame.draw.rect(surface, self.theme.panel_border, panel, width=1, border_radius=10)
        surface.blit(prompt, prompt_rect)
