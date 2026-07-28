"""Thin Space Invaders state integrated with the shared lifecycle."""
from __future__ import annotations
from typing import Protocol
import pygame

from games.space_invaders.space_invaders_result import SpaceInvadersResult
from games.space_invaders.space_invaders_snapshot import MatchStatus
from games.space_invaders.space_invaders_world import SpaceInvadersWorld
from states.base_state import BaseState
from states.game_over_state import GameOverContext


class SpaceInvadersGameplayView(Protocol):
    def render(self, surface: pygame.Surface, snapshot: object) -> None:
        ...


class SpaceInvadersState(BaseState):
    def __init__(self, state_manager: object, view: SpaceInvadersGameplayView) -> None:
        super().__init__(state_manager)
        self.world = SpaceInvadersWorld()
        self.view = view
        self._game_over_transition_sent = False
        self._left_pressed = False
        self._right_pressed = False

    def enter(self, data: dict[str, object] | None = None) -> None:
        del data
        self.world.restart()
        self._game_over_transition_sent = False
        self._left_pressed = False
        self._right_pressed = False

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_LEFT, pygame.K_a):
                self._left_pressed = True
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                self._right_pressed = True
            elif event.key in (pygame.K_SPACE, pygame.K_UP, pygame.K_w):
                self.world.request_fire()
            elif event.key == pygame.K_ESCAPE:
                self.state_manager.push("pause")
            elif event.key in (pygame.K_m, pygame.K_BACKSPACE):
                self.state_manager.replace("main_menu")
        elif event.type == pygame.KEYUP:
            if event.key in (pygame.K_LEFT, pygame.K_a):
                self._left_pressed = False
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                self._right_pressed = False
        self.world.set_move_axis(float(self._right_pressed) - float(self._left_pressed))

    def update(self, delta_time: float) -> None:
        self.world.update(delta_time)
        if self.world.match_status is MatchStatus.COMPLETED and not self._game_over_transition_sent:
            self._game_over_transition_sent = True
            result = SpaceInvadersResult.create(
                score=self.world.score,
                waves_completed=self.world.waves_completed,
                enemies_destroyed=self.world.enemies_destroyed,
                remaining_lives=self.world.player.lives,
                outcome=self.world.outcome,
                completion_reason=self.world.completion_reason,
            )
            self.state_manager.replace(
                "game_over",
                {"context": GameOverContext(result=result, restart_state="space_invaders")},
            )

    def render(self, surface: pygame.Surface) -> None:
        self.view.render(surface, self.world.snapshot())
