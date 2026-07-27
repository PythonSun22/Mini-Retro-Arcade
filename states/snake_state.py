"""Thin Snake state for the isolated backend vertical slice."""

from __future__ import annotations

import pygame

from games.snake.direction import Direction
from games.snake.snake_world import MatchStatus, SnakeSnapshot, SnakeWorld
from states.base_state import BaseState


class SnakeState(BaseState):
    """Translate input, update SnakeWorld, and provide diagnostic rendering."""

    BACKGROUND_COLOR = (18, 20, 28)
    GRID_COLOR = (48, 53, 66)
    SNAKE_COLOR = (104, 196, 120)
    HEAD_COLOR = (156, 232, 140)
    FOOD_COLOR = (234, 104, 104)
    TEXT_COLOR = (235, 235, 245)

    def __init__(self, state_manager: object) -> None:
        super().__init__(state_manager)
        self.world = SnakeWorld()
        self.font = pygame.font.Font(None, 28)

    def enter(self, data: dict[str, object] | None = None) -> None:
        del data
        self.world.restart()

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type != pygame.KEYDOWN:
            return

        direction = self._direction_for_key(event.key)
        if direction is not None:
            self.world.request_direction(direction)

        elif event.key == pygame.K_ESCAPE:
            self.state_manager.push("pause")

        elif event.key in (pygame.K_m, pygame.K_BACKSPACE):
            self.state_manager.replace("main_menu")

    def update(self, delta_time: float) -> None:
        self.world.update(delta_time)

    def render(self, surface: pygame.Surface) -> None:
        """Temporary diagnostic rendering pending Chat C presentation work."""
        snapshot = self.world.snapshot()
        self._render_diagnostic(surface, snapshot)

    @staticmethod
    def _direction_for_key(key: int) -> Direction | None:
        mapping = {
            pygame.K_UP: Direction.UP,
            pygame.K_w: Direction.UP,
            pygame.K_DOWN: Direction.DOWN,
            pygame.K_s: Direction.DOWN,
            pygame.K_LEFT: Direction.LEFT,
            pygame.K_a: Direction.LEFT,
            pygame.K_RIGHT: Direction.RIGHT,
            pygame.K_d: Direction.RIGHT,
        }
        return mapping.get(key)

    def _render_diagnostic(
        self,
        surface: pygame.Surface,
        snapshot: SnakeSnapshot,
    ) -> None:
        width, height = surface.get_size()
        hud_height = 72
        margin = 24
        available_width = width - margin * 2
        available_height = height - hud_height - margin * 2
        cell_size = max(
            1,
            min(
                available_width // snapshot.grid_width,
                available_height // snapshot.grid_height,
            ),
        )

        playfield_width = cell_size * snapshot.grid_width
        playfield_height = cell_size * snapshot.grid_height
        origin_x = (width - playfield_width) // 2
        origin_y = hud_height + (height - hud_height - playfield_height) // 2

        surface.fill(self.BACKGROUND_COLOR)

        for x in range(snapshot.grid_width + 1):
            line_x = origin_x + x * cell_size
            pygame.draw.line(
                surface,
                self.GRID_COLOR,
                (line_x, origin_y),
                (line_x, origin_y + playfield_height),
            )

        for y in range(snapshot.grid_height + 1):
            line_y = origin_y + y * cell_size
            pygame.draw.line(
                surface,
                self.GRID_COLOR,
                (origin_x, line_y),
                (origin_x + playfield_width, line_y),
            )

        if snapshot.food_position is not None:
            self._draw_cell(
                surface,
                snapshot.food_position,
                origin_x,
                origin_y,
                cell_size,
                self.FOOD_COLOR,
            )

        for index, position in enumerate(snapshot.snake_body):
            color = self.HEAD_COLOR if index == 0 else self.SNAKE_COLOR
            self._draw_cell(
                surface,
                position,
                origin_x,
                origin_y,
                cell_size,
                color,
            )

        status = f"Snake  |  Score: {snapshot.score}  |  Speed: {snapshot.speed_level}"
        if snapshot.match_status is MatchStatus.WAITING_TO_START:
            status += "  |  Press an arrow key or WASD to start"

        text = self.font.render(status, True, self.TEXT_COLOR)
        surface.blit(text, text.get_rect(center=(width // 2, 32)))

    @staticmethod
    def _draw_cell(
        surface: pygame.Surface,
        position: tuple[int, int],
        origin_x: int,
        origin_y: int,
        cell_size: int,
        color: tuple[int, int, int],
    ) -> None:
        x, y = position
        inset = max(1, cell_size // 10)
        rect = pygame.Rect(
            origin_x + x * cell_size + inset,
            origin_y + y * cell_size + inset,
            max(1, cell_size - inset * 2),
            max(1, cell_size - inset * 2),
        )
        pygame.draw.rect(surface, color, rect)
