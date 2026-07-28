"""Central application runtime for Minigame Arcade."""

from __future__ import annotations

import asyncio

import pygame

from arcade.state_manager import StateManager
from games.pong.pong_result import PongResult
from games.snake.snake_result import SnakeResult
from games.space_invaders.space_invaders_result import SpaceInvadersResult
from states.game_over_state import GameOverState, ResultPresenterRegistry
from states.main_menu_state import MainMenuState
from states.pause_state import PauseState
from states.pong_state import PongState
from states.snake_state import SnakeState
from states.space_invaders_state import SpaceInvadersState
from ui.pong_result_view import PongResultView
from ui.pong_view import PongView
from ui.snake_result_view import SnakeResultView
from ui.snake_view import SnakeView
from ui.space_invaders_result_view import SpaceInvadersResultView
from ui.space_invaders_view import SpaceInvadersView


class Application:
    """Owns the Pygame lifecycle and the single shared runtime loop."""

    WINDOW_SIZE = (960, 540)
    WINDOW_TITLE = "Minigame Arcade"
    TARGET_FPS = 60

    BACKGROUND_COLOR = (18, 20, 28)

    def __init__(self) -> None:
        """Initialize Pygame and create shared runtime resources."""
        pygame.init()

        self.screen = pygame.display.set_mode(self.WINDOW_SIZE)
        pygame.display.set_caption(self.WINDOW_TITLE)

        self.clock = pygame.time.Clock()
        self.state_manager = StateManager()
        self.running = True

        self.pong_view = PongView()
        self.snake_view = SnakeView()
        self.space_invaders_view = SpaceInvadersView()
        self.pong_result_view = PongResultView()
        self.snake_result_view = SnakeResultView()
        self.space_invaders_result_view = SpaceInvadersResultView()
        self.result_presenter_registry = self._create_result_presenter_registry()

        self._register_states()
        self.state_manager.replace("main_menu")

    async def run(self) -> None:
        """Run the application until a shutdown event is received."""
        try:
            while self.running:
                delta_time = self.clock.tick(self.TARGET_FPS) / 1000.0

                self._handle_events()
                self._update(delta_time)
                self._render()

                # Return control to the browser once per rendered frame.
                await asyncio.sleep(0)
        finally:
            self.shutdown()

    def _create_result_presenter_registry(self) -> ResultPresenterRegistry:
        """Create the application-scoped typed result presenter registry."""
        registry = ResultPresenterRegistry()
        registry.register(PongResult, self.pong_result_view)
        registry.register(SnakeResult, self.snake_result_view)
        registry.register(SpaceInvadersResult, self.space_invaders_result_view)
        return registry

    def _register_states(self) -> None:
        """Register all states available in the arcade shell."""
        self.state_manager.register(
            "main_menu",
            lambda manager: MainMenuState(manager),
        )

        self.state_manager.register(
            "pause",
            lambda manager: PauseState(manager),
        )

        self.state_manager.register(
            "game_over",
            lambda manager: GameOverState(
                manager,
                presenter_registry=self.result_presenter_registry,
            ),
        )

        self.state_manager.register(
            "pong",
            lambda manager: PongState(
                manager,
                view=self.pong_view,
            ),
        )

        self.state_manager.register(
            "snake",
            lambda manager: SnakeState(
                manager,
                view=self.snake_view,
            ),
        )

        self.state_manager.register(
            "space_invaders",
            lambda manager: SpaceInvadersState(
                manager,
                view=self.space_invaders_view,
            ),
        )

    def _handle_events(self) -> None:
        """Poll the single global event queue."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                continue

            self.state_manager.handle_event(event)

    def _update(self, delta_time: float) -> None:
        """Update the active application state."""
        self.state_manager.update(delta_time)

    def _render(self) -> None:
        """Render the current application frame."""
        self.screen.fill(self.BACKGROUND_COLOR)
        self.state_manager.render(self.screen)
        pygame.display.flip()

    def shutdown(self) -> None:
        """Release Pygame resources cleanly."""
        pygame.quit()
