"""Base lifecycle contract for all application states."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import pygame


class BaseState(ABC):
    """Abstract base class for every application state.

    States participate in the central application loop. They must never
    create their own permanent event, update, or rendering loops.
    """

    def __init__(self, state_manager: Any) -> None:
        self.state_manager = state_manager

    def enter(self, data: dict[str, Any] | None = None) -> None:
        """Run when this state becomes active."""
        del data

    def exit(self) -> None:
        """Run when this state is permanently removed."""

    def pause(self) -> None:
        """Run when another state is pushed above this state."""

    def resume(self, data: dict[str, Any] | None = None) -> None:
        """Run when this state becomes active again after an overlay closes."""
        del data

    @abstractmethod
    def handle_event(self, event: pygame.event.Event) -> None:
        """Handle one event forwarded by the application."""

    @abstractmethod
    def update(self, delta_time: float) -> None:
        """Update state behavior."""

    @abstractmethod
    def render(self, surface: pygame.Surface) -> None:
        """Render the state to the shared display surface."""