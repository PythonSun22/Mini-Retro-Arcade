"""Browser-compatible entry point for Minigame Arcade."""

from __future__ import annotations

# /// script
# dependencies = [
#     "pygame-ce",
# ]
# ///

import asyncio

# Keep pygame imported directly in main.py so Pygbag detects and preloads
# the browser-compatible pygame-ce package before project modules execute.
import pygame

from arcade.application import Application


async def main() -> None:
    """Create and run the central application."""
    application = Application()
    await application.run()


if __name__ == "__main__":
    asyncio.run(main())