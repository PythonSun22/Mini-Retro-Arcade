from __future__ import annotations

from dataclasses import FrozenInstanceError
import inspect
from pathlib import Path

import pygame
import pytest

from games.pong.pong_result import PongResult, PongWinner
from games.snake.snake_result import SnakeResult
from games.snake.snake_world import GameOverReason, MatchResult
from states.game_over_state import (
    GameOverContext,
    GameOverState,
    MissingResultPresenterError,
    ResultPresenterRegistry,
)
from states.pong_state import PongState
from states.snake_state import SnakeState


class RecordingManager:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, object] | None]] = []

    def replace(self, name: str, data: dict[str, object] | None = None) -> None:
        self.calls.append((name, data))


class RecordingPresenter:
    def __init__(self) -> None:
        self.calls: list[tuple[object, tuple[tuple[str, str], ...], int]] = []

    def render(self, surface, result, actions, selected_index) -> None:
        del surface
        self.calls.append((result, actions, selected_index))


def key_event(key: int) -> pygame.event.Event:
    return pygame.event.Event(pygame.KEYDOWN, key=key)


def registry_for(result_type: type[object], presenter=None):
    registry = ResultPresenterRegistry()
    registry.register(result_type, presenter or RecordingPresenter())
    return registry


def test_pong_result_is_typed_and_immutable() -> None:
    result = PongResult.create(player_score=5, ai_score=3, match_result="player")
    assert result.winner is PongWinner.PLAYER
    with pytest.raises(FrozenInstanceError):
        result.player_score = 9  # type: ignore[misc]


def test_pong_result_rejects_incomplete_match() -> None:
    with pytest.raises(ValueError):
        PongResult.create(player_score=1, ai_score=1, match_result=None)


def test_snake_result_is_typed_and_immutable() -> None:
    result = SnakeResult.create(
        score=70,
        speed_level=2,
        completion_reason=GameOverReason.WALL_COLLISION,
        outcome=MatchResult.LOSS,
    )
    assert not result.grid_completed
    with pytest.raises(FrozenInstanceError):
        result.score = 0  # type: ignore[misc]


def test_snake_grid_completion_is_a_win() -> None:
    result = SnakeResult.create(
        score=100,
        speed_level=3,
        completion_reason=GameOverReason.GRID_COMPLETED,
        outcome=MatchResult.WIN,
    )
    assert result.grid_completed


def test_snake_result_rejects_inconsistent_completion() -> None:
    with pytest.raises(ValueError):
        SnakeResult.create(
            score=100,
            speed_level=3,
            completion_reason=GameOverReason.GRID_COMPLETED,
            outcome=MatchResult.LOSS,
        )


def test_registry_resolves_by_exact_result_type() -> None:
    presenter = RecordingPresenter()
    registry = registry_for(PongResult, presenter)
    result = PongResult.create(player_score=5, ai_score=2, match_result="player")
    assert registry.get_presenter(result) is presenter


def test_registry_rejects_duplicate_result_type() -> None:
    registry = registry_for(PongResult)
    with pytest.raises(ValueError):
        registry.register(PongResult, RecordingPresenter())


def test_registry_rejects_unregistered_result_type() -> None:
    with pytest.raises(MissingResultPresenterError, match="Register it during application bootstrap"):
        ResultPresenterRegistry().get_presenter(object())


def test_game_over_delegates_opaque_result_to_registered_presenter() -> None:
    manager = RecordingManager()
    presenter = RecordingPresenter()
    result = object()
    state = GameOverState(manager, registry_for(object, presenter))
    state.enter({"context": GameOverContext(result=result, restart_state="pong")})

    state.render(object())

    assert presenter.calls[0][0] is result
    assert presenter.calls[0][2] == 0


def test_game_over_restart_uses_supplied_route() -> None:
    manager = RecordingManager()
    result = object()
    state = GameOverState(manager, registry_for(object))
    state.enter({"context": GameOverContext(result=result, restart_state="snake")})

    state.handle_event(key_event(pygame.K_RETURN))
    assert manager.calls == [("snake", None)]


def test_game_over_menu_uses_supplied_route() -> None:
    manager = RecordingManager()
    result = object()
    state = GameOverState(manager, registry_for(object))
    state.enter({
        "context": GameOverContext(
            result=result,
            restart_state="snake",
            menu_state="main_menu",
        )
    })

    state.handle_event(key_event(pygame.K_DOWN))
    state.handle_event(key_event(pygame.K_RETURN))
    assert manager.calls == [("main_menu", None)]


def test_escape_returns_to_menu() -> None:
    manager = RecordingManager()
    result = object()
    state = GameOverState(manager, registry_for(object))
    state.enter({"context": GameOverContext(result=result, restart_state="pong")})

    state.handle_event(key_event(pygame.K_ESCAPE))
    assert manager.calls == [("main_menu", None)]


def test_game_over_requires_context() -> None:
    state = GameOverState(RecordingManager(), ResultPresenterRegistry())
    with pytest.raises(ValueError):
        state.enter(None)
    with pytest.raises(TypeError):
        state.enter({"context": object()})


def test_game_over_fails_early_for_missing_presenter() -> None:
    state = GameOverState(RecordingManager(), ResultPresenterRegistry())
    with pytest.raises(MissingResultPresenterError, match="concrete result type"):
        state.enter({"context": GameOverContext(result=object(), restart_state="pong")})


def test_gameplay_state_constructors_do_not_accept_result_presenters() -> None:
    pong_parameters = inspect.signature(PongState.__init__).parameters
    snake_parameters = inspect.signature(SnakeState.__init__).parameters

    assert "result_presenter" not in pong_parameters
    assert "presenter" not in pong_parameters
    assert "result_presenter" not in snake_parameters
    assert "presenter" not in snake_parameters


@pytest.mark.parametrize(
    ("result", "restart_state", "presenter_type"),
    [
        (
            PongResult.create(
                player_score=5,
                ai_score=2,
                match_result="player",
            ),
            "pong",
            PongResult,
        ),
        (
            SnakeResult.create(
                score=70,
                speed_level=2,
                completion_reason=GameOverReason.WALL_COLLISION,
                outcome=MatchResult.LOSS,
            ),
            "snake",
            SnakeResult,
        ),
    ],
)
def test_correct_presenter_and_transitions_for_each_game(
    result: object,
    restart_state: str,
    presenter_type: type[object],
) -> None:
    manager = RecordingManager()
    presenter = RecordingPresenter()
    registry = ResultPresenterRegistry()
    registry.register(presenter_type, presenter)
    state = GameOverState(manager, registry)
    state.enter({
        "context": GameOverContext(
            result=result,
            restart_state=restart_state,
        )
    })

    state.render(object())
    assert presenter.calls[0][0] is result

    state.handle_event(key_event(pygame.K_RETURN))
    assert manager.calls[-1] == (restart_state, None)

    manager.calls.clear()
    state.enter({
        "context": GameOverContext(
            result=result,
            restart_state=restart_state,
        )
    })
    state.handle_event(key_event(pygame.K_DOWN))
    state.handle_event(key_event(pygame.K_RETURN))
    assert manager.calls == [("main_menu", None)]


def test_game_over_does_not_alter_immutable_result() -> None:
    manager = RecordingManager()
    presenter = RecordingPresenter()
    result = PongResult.create(
        player_score=5,
        ai_score=2,
        match_result="player",
    )
    original_value = result
    original_fields = (result.player_score, result.ai_score, result.winner)
    state = GameOverState(manager, registry_for(PongResult, presenter))

    state.enter({"context": GameOverContext(result=result, restart_state="pong")})
    state.render(object())

    assert presenter.calls[0][0] is original_value
    assert (result.player_score, result.ai_score, result.winner) == original_fields


def test_gameplay_states_do_not_import_ui_modules() -> None:
    states_root = Path(__file__).parents[1] / "states"
    for filename in ("pong_state.py", "snake_state.py"):
        source = (states_root / filename).read_text(encoding="utf-8")
        assert "from ui." not in source
        assert "import ui." not in source
