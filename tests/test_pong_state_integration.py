"""Integration tests for Pong state transitions."""

from __future__ import annotations

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from arcade.state_manager import StateManager
from games.pong.pong_world import PongWorld, RoundStatus
from states.game_over_state import GameOverState
from states.main_menu_state import MainMenuState
from states.pause_state import PauseState
from states.pong_state import PongState


@pytest.fixture(autouse=True)
def pygame_runtime() -> None:
    """Provide the display and font systems required by concrete states."""
    pygame.init()
    pygame.display.set_mode((960, 540))

    yield

    pygame.quit()


@pytest.fixture
def manager() -> StateManager:
    """Create a state manager with Pong-related states registered."""
    state_manager = StateManager()

    state_manager.register(
        "main_menu",
        lambda current_manager: MainMenuState(current_manager),
    )

    state_manager.register(
        "pong",
        lambda current_manager: PongState(current_manager),
    )

    state_manager.register(
        "pause",
        lambda current_manager: PauseState(current_manager),
    )

    state_manager.register(
        "game_over",
        lambda current_manager: GameOverState(current_manager),
    )

    return state_manager


def test_escape_pushes_pause_over_pong(
    manager: StateManager,
) -> None:
    manager.replace("pong")
    pong_state = manager.active_state

    assert isinstance(pong_state, PongState)

    escape_event = pygame.event.Event(
        pygame.KEYDOWN,
        key=pygame.K_ESCAPE,
    )
    manager.handle_event(escape_event)

    assert isinstance(manager.active_state, PauseState)
    assert manager.stack_depth == 2


def test_pause_resume_preserves_same_pong_state_and_world(
    manager: StateManager,
) -> None:
    manager.replace("pong")
    pong_state = manager.active_state

    assert isinstance(pong_state, PongState)

    pong_state.world.player_score = 2
    pong_state.world.ai_score = 1
    original_world = pong_state.world

    manager.push("pause")
    manager.pop()

    assert manager.active_state is pong_state
    assert pong_state.world is original_world
    assert pong_state.world.player_score == 2
    assert pong_state.world.ai_score == 1
    assert manager.stack_depth == 1


def test_pause_clears_held_player_input(
    manager: StateManager,
) -> None:
    manager.replace("pong")
    pong_state = manager.active_state

    assert isinstance(pong_state, PongState)

    key_down = pygame.event.Event(
        pygame.KEYDOWN,
        key=pygame.K_DOWN,
    )
    manager.handle_event(key_down)

    pong_state.update(0.1)
    assert pong_state.world.player_paddle.velocity_y > 0.0

    manager.push("pause")

    assert pong_state.world.player_paddle.velocity_y == 0.0


def test_return_to_menu_discards_paused_pong_match(
    manager: StateManager,
) -> None:
    manager.replace("pong")
    pong_state = manager.active_state

    assert isinstance(pong_state, PongState)

    pong_state.world.player_score = 3

    manager.push("pause")
    manager.replace("main_menu")

    assert isinstance(manager.active_state, MainMenuState)
    assert manager.stack_depth == 1


def test_match_completion_transitions_to_game_over(
    manager: StateManager,
) -> None:
    manager.replace("pong")
    pong_state = manager.active_state

    assert isinstance(pong_state, PongState)

    pong_state.world = PongWorld(winning_score=1)
    pong_state.world.start_serve()

    pong_state.world.ball.x = float(
        pong_state.world.WIDTH + 1
    )
    pong_state.world.ball.velocity_x = (
        pong_state.world.BALL_SPEED_X
    )

    manager.update(0.0)

    active_state = manager.active_state

    assert isinstance(active_state, GameOverState)
    assert active_state.game_name == "Pong"
    assert active_state.result == "player"
    assert active_state.player_score == 1
    assert active_state.opponent_score == 0
    assert active_state.restart_state == "pong"


def test_game_over_transition_occurs_only_once(
    manager: StateManager,
) -> None:
    manager.replace("pong")
    pong_state = manager.active_state

    assert isinstance(pong_state, PongState)

    pong_state.world = PongWorld(winning_score=1)
    pong_state.world.start_serve()
    pong_state.world.ball.x = float(
        pong_state.world.WIDTH + 1
    )

    manager.update(0.0)

    assert isinstance(manager.active_state, GameOverState)
    assert manager.stack_depth == 1

    manager.update(0.0)

    assert isinstance(manager.active_state, GameOverState)
    assert manager.stack_depth == 1


def test_restart_from_game_over_creates_fresh_pong_state(
    manager: StateManager,
) -> None:
    manager.replace("pong")
    original_pong = manager.active_state

    assert isinstance(original_pong, PongState)

    original_pong.world.player_score = 5

    manager.replace(
        "game_over",
        {
            "game_name": "Pong",
            "result": "player",
            "player_score": 5,
            "opponent_score": 2,
            "restart_state": "pong",
        },
    )

    restart_event = pygame.event.Event(
        pygame.KEYDOWN,
        key=pygame.K_RETURN,
    )
    manager.handle_event(restart_event)

    restarted_pong = manager.active_state

    assert isinstance(restarted_pong, PongState)
    assert restarted_pong is not original_pong
    assert restarted_pong.world.player_score == 0
    assert restarted_pong.world.ai_score == 0
    assert (
        restarted_pong.world.round_status
        is RoundStatus.WAITING_TO_SERVE
    )


def test_game_over_menu_action_returns_to_main_menu(
    manager: StateManager,
) -> None:
    manager.replace(
        "game_over",
        {
            "game_name": "Pong",
            "result": "ai",
            "player_score": 2,
            "opponent_score": 5,
            "restart_state": "pong",
        },
    )

    down_event = pygame.event.Event(
        pygame.KEYDOWN,
        key=pygame.K_DOWN,
    )
    enter_event = pygame.event.Event(
        pygame.KEYDOWN,
        key=pygame.K_RETURN,
    )

    manager.handle_event(down_event)
    manager.handle_event(enter_event)

    assert isinstance(manager.active_state, MainMenuState)
    assert manager.stack_depth == 1