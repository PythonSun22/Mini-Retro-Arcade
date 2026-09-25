# Browser launch screen

`arcade.tmpl` is derived from the Pygbag **0.9.3** default template served at
https://pygame-web.github.io/cdn/0.9.3/default.tmpl (the matching local build cache).
The installed 0.9.3 CLI supports `--template` with a local file path. CI and
`requirements-dev.txt` both pin this version. Recheck the template/runtime contract
before upgrading Pygbag.

From the repository root, with the development environment activated:

```powershell
python -m pygbag --build --template web/arcade.tmpl .
python -m pygbag --template web/arcade.tmpl .
```

On Windows without activation, use `.venv\Scripts\python.exe` instead of `python`.
The server prints its local URL (normally http://localhost:8000). Build output
remains in ignored `build/web`; GitHub Actions publishes this directory on pushes
to `main`, with the existing Pages deployment job unchanged.

The template retains `site`/`pythons.js`, template substitutions, archive extraction,
`platform.run_main`, preload-counter wait, `MM.UME` audio gate, top-level handler,
`shell.source`, canvas elements, resize hooks, and console widgets. After preloading,
Python enables the button and waits for its click flag before continuing through
the original media gate. The trusted click bubbles to Pygbag's own handlers; the
template never fabricates media engagement. The launch panel stays visible during
startup and hides after `shell.source` returns, then focuses the game canvas.

Runtime download progress uses Pygbag's existing status/progress elements. The
custom animated bar is indeterminate, with no invented percentage. All decoration
is inline text/CSS; no new font, image, or JavaScript dependency is downloaded.
Reduced-motion preferences disable animation.

Python startup exceptions are re-raised after showing a failure message; unhandled
JavaScript errors also show it. Use the diagnostics link (reloads with `#debug`)
and browser developer console for tracebacks or stalled network downloads. The
normal Pygbag runtime and dependencies still require network access on first load.

## Interactive verification

These checks require a connected browser and have not been verified in this environment:

- Fresh load: branding, disabled button, loading animation, and actual runtime progress.
- Early page click must not skip ENTER ARCADE; readiness enables the button.
- Button click and keyboard activation start the Pygame main menu and focus the canvas.
- Launch Pong, Snake, and Space Invaders; check controls, pause, restart, and return to menu.
- Check audio with browser autoplay restrictions, especially Safari, and reload/re-entry.
- Check narrow/landscape layouts, reduced motion, and `#debug` console visibility.
- Block a runtime request to check diagnostic access; inspect Python/JavaScript errors.
- After an authorized push, verify the Pages workflow and deployed project-subpath URL.

No GitHub Pages deployment has been performed as part of this change.

## Local validation results

- Pygbag 0.9.3 custom-template build completed; local server returned HTTP 200
  with the custom branding.
- Generated embedded Python parses successfully, template substitutions resolve,
  and HTML IDs are unique. `git diff --check` passed.
- Plain pytest stops during collection because the existing Pygame stub lacks
  `surface`. Preloading installed Pygame with dummy SDL video/audio drivers runs
  the suite: **91 passed, 9 failed**. The failures are existing integration test
  constructors missing the required `view` argument (eight Pong, one Snake).
  Framework, gameplay, and test files were not modified.
- Browser automation reported no available browsers, so visual, gesture, audio,
  and gameplay verification remains manual as listed above.
