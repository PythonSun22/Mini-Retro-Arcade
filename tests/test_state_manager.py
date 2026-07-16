"""Tests for the stack-based application state manager."""

from __future__ import annotations

import os
from typing import Any

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame
import pytest

from arcade.state_manager import StateManager
from states.base_state import BaseState


class TrackingState(BaseState):
    """Minimal state that records lifecycle calls for testing."""

    def __init__(
        self,
        state_manager: StateManager,
        name: str,
    ) -> None:
        super().__init__(state_manager)

        self.name = name
        self.lifecycle: list[str] = []
        self.received_data: list[dict[str, Any] | None] = []
        self.event_count = 0
        self.update_count = 0
        self.render_count = 0

    def enter(self, data: dict[str, Any] | None = None) -> None:
        self.lifecycle.append("enter")
        self.received_data.append(data)

    def exit(self) -> None:
        self.lifecycle.append("exit")

    def pause(self) -> None:
        self.lifecycle.append("pause")

    def resume(self, data: dict[str, Any] | None = None) -> None:
        self.lifecycle.append("resume")
        self.received_data.append(data)

    def handle_event(self, event: pygame.event.Event) -> None:
        del event
        self.event_count += 1

    def update(self, delta_time: float) -> None:
        del delta_time
        self.update_count += 1

    def render(self, surface: pygame.Surface) -> None:
        del surface
        self.render_count += 1


@pytest.fixture(autouse=True)
def pygame_runtime() -> None:
    """Initialize a minimal headless Pygame runtime for each test."""
    pygame.init()
    yield
    pygame.quit()


@pytest.fixture
def manager() -> StateManager:
    """Return a manager with three tracking states registered."""
    state_manager = StateManager()

    state_manager.register(
        "menu",
        lambda current_manager: TrackingState(
            current_manager,
            "menu",
        ),
    )
    state_manager.register(
        "game",
        lambda current_manager: TrackingState(
            current_manager,
            "game",
        ),
    )
    state_manager.register(
        "pause",
        lambda current_manager: TrackingState(
            current_manager,
            "pause",
        ),
    )

    return state_manager


def test_replace_activates_root_state(manager: StateManager) -> None:
    manager.replace("menu", {"source": "startup"})

    active = manager.active_state

    assert isinstance(active, TrackingState)
    assert active.name == "menu"
    assert active.lifecycle == ["enter"]
    assert active.received_data == [{"source": "startup"}]
    assert manager.stack_depth == 1


def test_replace_exits_every_existing_state(
    manager: StateManager,
) -> None:
    manager.replace("game")
    game = manager.active_state

    manager.push("pause")
    pause = manager.active_state

    manager.replace("menu")

    assert isinstance(game, TrackingState)
    assert isinstance(pause, TrackingState)

    assert game.lifecycle == ["enter", "pause", "exit"]
    assert pause.lifecycle == ["enter", "exit"]

    active = manager.active_state
    assert isinstance(active, TrackingState)
    assert active.name == "menu"
    assert manager.stack_depth == 1


def test_push_pauses_active_state(manager: StateManager) -> None:
    manager.replace("game")
    game = manager.active_state

    manager.push("pause")

    assert isinstance(game, TrackingState)
    assert game.lifecycle == ["enter", "pause"]

    active = manager.active_state
    assert isinstance(active, TrackingState)
    assert active.name == "pause"
    assert active.lifecycle == ["enter"]
    assert manager.stack_depth == 2


def test_pop_exits_overlay_and_resumes_previous_state(
    manager: StateManager,
) -> None:
    manager.replace("game")
    game = manager.active_state

    manager.push("pause")
    pause = manager.active_state

    manager.pop({"reason": "resume"})

    assert isinstance(game, TrackingState)
    assert isinstance(pause, TrackingState)

    assert pause.lifecycle == ["enter", "exit"]
    assert game.lifecycle == ["enter", "pause", "resume"]
    assert game.received_data[-1] == {"reason": "resume"}
    assert manager.active_state is game
    assert manager.stack_depth == 1


def test_only_active_state_receives_events_and_updates(
    manager: StateManager,
) -> None:
    manager.replace("game")
    game = manager.active_state

    manager.push("pause")
    pause = manager.active_state

    event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)

    manager.handle_event(event)
    manager.update(1.0 / 60.0)

    assert isinstance(game, TrackingState)
    assert isinstance(pause, TrackingState)

    assert game.event_count == 0
    assert game.update_count == 0
    assert pause.event_count == 1
    assert pause.update_count == 1


def test_render_draws_entire_stack_in_order(
    manager: StateManager,
) -> None:
    surface = pygame.Surface((320, 180))

    manager.replace("game")
    game = manager.active_state

    manager.push("pause")
    pause = manager.active_state

    manager.render(surface)

    assert isinstance(game, TrackingState)
    assert isinstance(pause, TrackingState)

    assert game.render_count == 1
    assert pause.render_count == 1


def test_duplicate_registration_is_rejected(
    manager: StateManager,
) -> None:
    with pytest.raises(ValueError, match="already registered"):
        manager.register(
            "menu",
            lambda current_manager: TrackingState(
                current_manager,
                "duplicate",
            ),
        )


def test_unknown_state_transition_is_rejected(
    manager: StateManager,
) -> None:
    with pytest.raises(KeyError, match="Unknown state"):
        manager.replace("missing")


def test_empty_state_name_is_rejected(
    manager: StateManager,
) -> None:
    with pytest.raises(ValueError, match="cannot be empty"):
        manager.register(
            "   ",
            lambda current_manager: TrackingState(
                current_manager,
                "invalid",
            ),
        )


def test_pop_from_empty_stack_is_rejected(
    manager: StateManager,
) -> None:
    with pytest.raises(RuntimeError, match="empty state stack"):
        manager.pop()