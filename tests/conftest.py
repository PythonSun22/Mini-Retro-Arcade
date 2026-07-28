"""Minimal pygame stub for isolated backend contract tests."""

from __future__ import annotations

import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class Event:
    def __init__(self, event_type: int, **attributes: object) -> None:
        self.type = event_type
        for name, value in attributes.items():
            setattr(self, name, value)


pygame = types.ModuleType("pygame")
pygame.KEYDOWN = 1
pygame.KEYUP = 2
pygame.K_UP = 10
pygame.K_w = 11
pygame.K_DOWN = 12
pygame.K_s = 13
pygame.K_RETURN = 14
pygame.K_SPACE = 15
pygame.K_ESCAPE = 16
pygame.K_LEFT = 17
pygame.K_a = 18
pygame.K_RIGHT = 19
pygame.K_d = 20
pygame.K_m = 21
pygame.K_BACKSPACE = 22
pygame.Surface = object
pygame.event = types.SimpleNamespace(Event=Event)
sys.modules.setdefault("pygame", pygame)
