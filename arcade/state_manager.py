"""Stack-based application state manager."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pygame

from states.base_state import BaseState


StateFactory = Callable[["StateManager"], BaseState]


class StateManager:
    """Registers, activates, and coordinates application states."""

    def __init__(self) -> None:
        self._factories: dict[str, StateFactory] = {}
        self._stack: list[BaseState] = []

    @property
    def active_state(self) -> BaseState | None:
        """Return the state currently receiving input and updates."""
        if not self._stack:
            return None

        return self._stack[-1]

    @property
    def stack_depth(self) -> int:
        """Return the number of active and paused states."""
        return len(self._stack)

    def register(self, name: str, factory: StateFactory) -> None:
        """Register a state factory under a unique name."""
        normalized_name = self._normalize_name(name)

        if normalized_name in self._factories:
            raise ValueError(f"State already registered: {normalized_name}")

        self._factories[normalized_name] = factory

    def replace(
        self,
        name: str,
        data: dict[str, Any] | None = None,
    ) -> None:
        """Remove every current state and activate a new root state."""
        new_state = self._create_state(name)

        while self._stack:
            removed_state = self._stack.pop()
            removed_state.exit()

        self._stack.append(new_state)
        new_state.enter(data)

    def push(
        self,
        name: str,
        data: dict[str, Any] | None = None,
    ) -> None:
        """Pause the active state and push another state above it."""
        new_state = self._create_state(name)

        current_state = self.active_state
        if current_state is not None:
            current_state.pause()

        self._stack.append(new_state)
        new_state.enter(data)

    def pop(
        self,
        data: dict[str, Any] | None = None,
    ) -> None:
        """Remove the active state and resume the state beneath it."""
        if not self._stack:
            raise RuntimeError("Cannot pop from an empty state stack.")

        removed_state = self._stack.pop()
        removed_state.exit()

        resumed_state = self.active_state
        if resumed_state is not None:
            resumed_state.resume(data)

    def handle_event(self, event: pygame.event.Event) -> None:
        """Forward an event to the active state."""
        current_state = self.active_state

        if current_state is not None:
            current_state.handle_event(event)

    def update(self, delta_time: float) -> None:
        """Update only the active state."""
        current_state = self.active_state

        if current_state is not None:
            current_state.update(delta_time)

    def render(self, surface: pygame.Surface) -> None:
        """Render all states in stack order.

        Rendering the full stack allows overlay states, such as Pause,
        to draw over the paused game state.
        """
        for state in self._stack:
            state.render(surface)

    def _create_state(self, name: str) -> BaseState:
        """Create a registered state through its factory."""
        normalized_name = self._normalize_name(name)

        try:
            factory = self._factories[normalized_name]
        except KeyError as error:
            raise KeyError(
                f"Unknown state: {normalized_name}. "
                f"Registered states: {sorted(self._factories)}"
            ) from error

        state = factory(self)

        if not isinstance(state, BaseState):
            raise TypeError(
                f"Factory for '{normalized_name}' did not return a BaseState."
            )

        return state

    @staticmethod
    def _normalize_name(name: str) -> str:
        """Normalize and validate a state registration name."""
        normalized_name = name.strip().lower()

        if not normalized_name:
            raise ValueError("State name cannot be empty.")

        return normalized_name