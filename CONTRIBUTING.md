# Contributing to SessionGlow

SessionGlow provides ambient status lights for OpenCode agents. Contributions should help users see task progress and attention requests with less distraction. Session management, terminal management and agent orchestration are outside the current scope.

English and Chinese issues and pull requests are welcome.

## Development environment

The verified desktop target is Ubuntu 22.04 / GNOME / X11, with Python 3.10, PyQt5 and OpenCode 1.18.31. Install development dependencies:

```bash
sudo apt install python3-pyqt5 pyflakes3 desktop-file-utils fonts-noto-cjk ffmpeg
```

Use Node.js 22 for plugin tests. The app uses Ubuntu's `/usr/bin/python3`, so activating a Python virtual environment does not change the launcher.

```bash
./run.sh --demo
/usr/bin/python3 install.py
```

Restart the actual OpenCode terminal/server process after installing or modifying its plugin. Use temporary test sessions; do not interrupt active user tasks.

## Checks

```bash
/usr/bin/python3 -m unittest discover -s tests -p 'test_*.py' -v
node --test tests/plugin.test.mjs
/usr/bin/python3 -m pyflakes sessionglow tests scripts install.py
desktop-file-validate packaging/sessionglow.desktop
git diff --check
/usr/bin/python3 scripts/build_deb.py
```

Python rendering tests run offscreen. They do not capture your desktop. Installed-package integration tests modify a disposable Ubuntu container, never the host package database:

```bash
docker run --rm -v "$PWD:/src:ro" ubuntu:22.04 bash -c \
  'apt-get update && bash /src/scripts/smoke_deb.sh /src/dist/sessionglow_*_amd64.deb'
```

To verify the plugin with an actual OpenCode server, start SessionGlow and run:

```bash
/usr/bin/python3 tests/live_opencode.py
```

This creates and removes temporary main/subagent sessions using short local shell commands. It does not request a model. Desktop interaction checks require X11 and `xdotool`:

```bash
PYTHONPATH=. /usr/bin/python3 tests/smoke_desktop.py
```

This briefly moves/clicks its own panel and restores the pointer and focus. Run it while you are not using the mouse.

## Code map

| Location | Responsibility |
| --- | --- |
| `plugin/sessionglow.mjs` | OpenCode event handling, bounded history restore, snapshots and heartbeats |
| `sessionglow/model.py` | Ordering, parent/child aggregation, persistence and connection expiry |
| `sessionglow/server.py` | Bounded HTTP receiver on loopback; GUI consumes a queue |
| `sessionglow/motion.py` | Continuous animation parameters, independent of Qt |
| `sessionglow/panel.py` | Qt floating panel, tray, settings and tube drawing |
| `sessionglow/integration.py` | Safe per-user plugin installation, upgrades and removal |
| `scripts/build_deb.py` / `packaging/` | Deterministic package assembly and system launcher |
| `.github/workflows/ci.yml` | Tests, lint, package verification and tagged releases |

## Debugging session events

Use `curl -s http://127.0.0.1:8790/health` to check the actual server endpoint, PID, project and visible sessions. `connections` counts project plugin instances, not servers. OpenChamber may use a dynamically assigned backend port.

Add focused event tests in `tests/plugin.test.mjs` or aggregation tests in `tests/test_model.py`. Cover ordering, parent/child relations and terminal errors when they are affected. A generic tool error is not a terminal task failure, and a lost connection is not task completion.

Do not log or send prompt bodies, model responses, tool arguments or credentials. Use synthetic titles and messages in tests and examples. Metadata reads during bootstrap must not delay or overwrite live state.

## New platforms

Start with a roadmap issue and record the exact OS, desktop, session type, scaling and display arrangement. Validate tray behavior, always-on-top, drag/restore, multi-monitor positioning, rendering and shutdown. Keep unverified platforms marked **Untested**; a passing offscreen container test is not a desktop compatibility test.

Use existing Qt behavior before adding native code. Package work should include clean install, upgrade and uninstall tests. Do not bundle third-party libraries without checking their redistribution terms. SessionGlow's MIT license applies to its own code; Python, PyQt5 and Qt retain their respective licenses.

## Pull requests

- Describe the user-visible problem and the final behavior, including screenshots or a short synthetic clip for visual changes.
- Keep changes focused and follow the existing Python/JavaScript style. Prefer standard-library solutions.
- Add meaningful regression tests for changed behavior and run the relevant checks.
- Update both `README.md` and `README.zh-CN.md` when user-facing instructions change.
- Use concise commit messages. Existing commits use `文档：…`; English messages such as `docs: clarify server restart` are also welcome.
- Never commit local session caches, credentials, generated `.deb` files or private transcripts.

## Release maintainers

Set `sessionglow.__version__`, update `docs/releases/vX.Y.Z.md`, run the checks, then push a matching annotated `vX.Y.Z` tag. CI verifies the version, tests the package and publishes the tested `.deb` plus `SHA256SUMS`. A failed build never publishes a release.

The first release also creates the three scoped roadmap issues from `docs/roadmap/`. See `scripts/publish_roadmap.py` for the idempotent publisher. Repository About/Topics and the Social Preview image require repository administration access; see `docs/RELEASE_CHECKLIST.md`.
