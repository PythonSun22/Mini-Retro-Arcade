## Current Implementation Status

### Architectural Baseline

The application uses a single shared asynchronous runtime compatible with both
desktop Python and Pygbag browser execution.

The runtime owns:

- One Pygame initialization path
- One display surface
- One frame clock
- One event-polling cycle
- One asynchronous application loop
- One stack-based state manager

Each frame yields through `await asyncio.sleep(0)` to remain compatible with
the browser runtime.

### Implemented States

- Main Menu
- Pong
- Snake placeholder
- Space Invaders placeholder
- Pause
- Game Over

### Pong

Pong is the first complete game and serves as the reference implementation for
future game modules.

The Pong backend is separated into:

```text
PongState
├── PongWorld
├── Paddle
├── AIPaddle
├── Ball
└── PongRules

### Local Execution
python main.py

### Browser Execution
python -m pygbag .


Troubleshooting note:

## Pygbag Notes

- Pygbag treats the final command-line argument as the application path.
- `pygbag.ini` must contain a valid `[DEPENDENCIES]` section.
- Root-level ignored directories use leading slashes, such as `/.venv`.
- `pygame` is intentionally imported directly in `main.py` so Pygbag detects
  and loads the browser-compatible dependency.
- A gray browser canvas usually indicates a Python exception. Append `/#debug`
  to the local URL and inspect the browser console.