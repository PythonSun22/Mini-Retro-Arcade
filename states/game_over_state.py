"""Shared game-over lifecycle state."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import pygame

from states.base_state import BaseState


GAME_OVER_ACTIONS: tuple[tuple[str, str], ...] = (
    ("Restart", "restart"),
    ("Return to Main Menu", "main_menu"),
)


class ResultPresenter(Protocol):
    """Structural frontend contract for one game-specific result presenter."""

    def render(
        self,
        surface: pygame.Surface,
        result: object,
        actions: tuple[tuple[str, str], ...],
        selected_index: int,
    ) -> None:
        """Render one completed-game result and the shared action choices."""
        ...


class MissingResultPresenterError(LookupError):
    """Raised when no presenter is registered for a concrete result type."""


class ResultPresenterRegistry:
    """Small application-level registry keyed by exact immutable result type."""

    def __init__(self) -> None:
        self._presenters: dict[type[object], ResultPresenter] = {}

    def register(
        self,
        result_type: type[object],
        presenter: ResultPresenter,
    ) -> None:
        if result_type in self._presenters:
            raise ValueError(
                f"A result presenter is already registered for "
                f"{result_type.__module__}.{result_type.__qualname__}."
            )
        self._presenters[result_type] = presenter

    def get_presenter(self, result: object) -> ResultPresenter:
        """Return the presenter registered for exactly ``type(result)``."""
        result_type = type(result)
        try:
            return self._presenters[result_type]
        except KeyError as error:
            qualified_name = (
                f"{result_type.__module__}.{result_type.__qualname__}"
            )
            raise MissingResultPresenterError(
                "No result presenter is registered for concrete result type "
                f"{qualified_name}. Register it during application bootstrap "
                "before entering GameOverState."
            ) from error


@dataclass(frozen=True)
class GameOverContext:
    """Immutable result and transition data required by GameOverState."""

    result: object
    restart_state: str
    menu_state: str = "main_menu"

    def __post_init__(self) -> None:
        if not self.restart_state.strip():
            raise ValueError("restart_state cannot be empty.")
        if not self.menu_state.strip():
            raise ValueError("menu_state cannot be empty.")


class GameOverState(BaseState):
    """Coordinate shared completion input, routing, and presenter delegation."""

    def __init__(
        self,
        state_manager: object,
        presenter_registry: ResultPresenterRegistry,
    ) -> None:
        super().__init__(state_manager)
        self._presenter_registry = presenter_registry
        self._context: GameOverContext | None = None
        self._presenter: ResultPresenter | None = None
        self.selected_index = 0

    def enter(self, data: dict[str, object] | None = None) -> None:
        if data is None:
            raise ValueError("GameOverState requires transition data.")

        context = data.get("context")
        if not isinstance(context, GameOverContext):
            raise TypeError("GameOverState requires a GameOverContext.")

        # Resolve only by concrete result type. The state never inspects fields.
        presenter = self._presenter_registry.get_presenter(context.result)
        self._context = context
        self._presenter = presenter
        self.selected_index = 0

    def exit(self) -> None:
        self._context = None
        self._presenter = None

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type != pygame.KEYDOWN:
            return

        if event.key in (pygame.K_UP, pygame.K_w):
            self.selected_index = (
                self.selected_index - 1
            ) % len(GAME_OVER_ACTIONS)
        elif event.key in (pygame.K_DOWN, pygame.K_s):
            self.selected_index = (
                self.selected_index + 1
            ) % len(GAME_OVER_ACTIONS)
        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
            self._activate_selected_action()
        elif event.key == pygame.K_ESCAPE:
            self._return_to_menu()

    def update(self, delta_time: float) -> None:
        del delta_time

    def render(self, surface: pygame.Surface) -> None:
        context = self._require_context()
        presenter = self._require_presenter()
        presenter.render(
            surface,
            context.result,
            GAME_OVER_ACTIONS,
            self.selected_index,
        )

    def _activate_selected_action(self) -> None:
        _, action = GAME_OVER_ACTIONS[self.selected_index]
        if action == "restart":
            context = self._require_context()
            self.state_manager.replace(context.restart_state)
            return
        self._return_to_menu()

    def _return_to_menu(self) -> None:
        context = self._require_context()
        self.state_manager.replace(context.menu_state)

    def _require_context(self) -> GameOverContext:
        if self._context is None:
            raise RuntimeError("GameOverState has not received its context.")
        return self._context

    def _require_presenter(self) -> ResultPresenter:
        if self._presenter is None:
            raise RuntimeError("GameOverState has not resolved its presenter.")
        return self._presenter
