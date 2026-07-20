"""Shared visual theme for Minigame Arcade."""

from __future__ import annotations

from dataclasses import dataclass


Color = tuple[int, int, int]


@dataclass(frozen=True)
class ArcadeTheme:
    """Centralized colors and spacing used by shared UI views."""

    background: Color = (12, 15, 24)
    panel: Color = (24, 29, 44)
    panel_border: Color = (68, 78, 108)
    text_primary: Color = (241, 244, 255)
    text_secondary: Color = (157, 166, 193)
    accent: Color = (255, 211, 92)
    accent_soft: Color = (106, 205, 255)
    shadow: Color = (5, 7, 12)

    outer_margin: int = 44
    panel_radius: int = 18
    item_height: int = 58
    item_spacing: int = 14


DEFAULT_THEME = ArcadeTheme()
