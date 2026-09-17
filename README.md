<div align="center">

<img src="icon.svg" width="68" height="68" alt="SessionGlow logo" />

# SessionGlow

**Ambient status lights for your OpenCode agents.**

See which agents are working, done, failed, or waiting for you<br />
without switching terminal tabs.

**English** · [简体中文](README.zh-CN.md)

<img src="docs/assets/sessionglow-demo.gif" width="420" alt="Four session lights. A working session requests permission, receives confirmation, resumes work, and completes." />

🔵 Working　 🟡 Needs you　 🟢 Done　 🔴 Failed

<sub>12-second synthetic scenario rendered by the app. “Approved” illustrates a user response; the panel does not grant permissions.</sub>

[![Build](https://github.com/YidaHao/SessionGlow/actions/workflows/ci.yml/badge.svg)](https://github.com/YidaHao/SessionGlow/actions/workflows/ci.yml)
[![MIT](https://img.shields.io/badge/license-MIT-8B5CF6)](LICENSE)
[![Linux](https://img.shields.io/badge/platform-Linux-E95420)](#compatibility)
[![Latest release](https://img.shields.io/github/v/release/YidaHao/SessionGlow)](https://github.com/YidaHao/SessionGlow/releases/latest)

[Download v0.1.0](https://github.com/YidaHao/SessionGlow/releases/tag/v0.1.0) · [24 fps demo](docs/assets/sessionglow-demo.webm) · [Installation](docs/INSTALL.md) · [Usage](docs/USAGE.md)

</div>

## Why SessionGlow?

When several agents run in parallel, checking every terminal for completion or a permission prompt becomes another task. SessionGlow keeps a small status light for each main session in a movable, always-on-top panel.

- **Event-driven:** task, failure, permission and question events supply the state. There is no CPU polling or terminal-output guessing.
- **One light, one session:** subagent activity and attention requests roll up into their parent session.
- **Local by design:** the plugin talks to the panel over localhost, sending a small session summary.

All animation stays inside the panel. Create tasks and answer permissions in OpenCode or OpenChamber.

## What the lights mean

| State | Animation | Meaning |
| --- | --- | --- |
| 🔵 Working | Five gently interweaving currents with drifting particles | Working or automatically retrying |
| 🟡 Needs you | Full waveforms with more irregular jitter | Waiting for permission or an answer |
| 🟢 Done | Slowly flowing green liquid; no electricity or particles | The task has finished |
| 🔴 Failed | A nearly straight, slightly trembling current; particles stop | Terminal failure or cancellation |

Transitions take about **0.8 seconds** and continue from the current frame when interrupted. Gray means no reliable result is available. Disconnection preserves and dims the last state; it is not treated as completion.

## Quick start

### Ubuntu package — recommended

Download [`sessionglow_0.1.0_amd64.deb`](https://github.com/YidaHao/SessionGlow/releases/download/v0.1.0/sessionglow_0.1.0_amd64.deb) from the release, then:

```bash
sudo apt install ./sessionglow_0.1.0_amd64.deb
sessionglow
```

Or open **SessionGlow** from your applications menu. A normal first launch registers the OpenCode plugin for the current user. **Restart the OpenCode process you actually use** to load it, then start a task. The panel and detailed usage guide currently use Chinese labels; this README covers the essentials in English.

| Your setup | Restart after plugin installation or upgrade |
| --- | --- |
| OpenCode terminal | Exit, then run `opencode -c` in your project directory |
| Standalone `opencode serve` | Wait for tasks to finish and restart the same service with its original arguments and credentials |
| OpenChamber managed backend | Wait for tasks to finish, then `openchamber restart --port 3000` (your web UI port) |
| OpenChamber with an external server | Restart the external OpenCode service; a browser refresh cannot reload its plugin |

OpenChamber may use a dynamic backend port rather than 4096. See [installation and integration](docs/INSTALL.md) for authentication and connection details. AppImage is planned, not shipped in v0.1.0.

Preview without connecting an agent:

```bash
sessionglow --demo
```

### Upgrade and uninstall

```bash
# Close the panel, install the newer package, then reopen it and restart OpenCode.
sudo apt install ./sessionglow_X.Y.Z_amd64.deb

# Remove your plugin entry before removing the package.
sessionglow --uninstall-plugin
sudo apt remove sessionglow
```

Restart OpenCode after removal. Settings and history remain in your home directory. If you remove the package first, its managed user plugin becomes inert; remove `~/.config/opencode/plugins/sessionglow.js` manually. No package script edits other users' home directories. [Complete lifecycle instructions](docs/INSTALL.md).

## Core features

- **Recent tasks in a stable order:** show 5 main sessions by default, configurable from 1 to 12. Tool events and heartbeats do not reorder them.
- **A compact desktop panel:** drag the title bar, toggle always-on-top, hide to the tray, and remember the window position.
- **Adjustable effects:** change frame rate, opacity and intensity. Hidden panels stop rendering.
- **Multiple local instances:** aggregate terminal, standalone server and OpenChamber sessions that load the plugin.
- **Reconnect and restore:** keep bounded local summaries and recover via heartbeats. Completed and failed sessions remain visible until displaced by more recent tasks.

## Event-driven architecture

OpenCode's plugin handles task and attention events, then posts bounded session snapshots to the panel at `127.0.0.1:8790`. A standard-library HTTP server queues updates for the Qt thread; the session model aggregates children, orders rows and stores recent summaries. The renderer interpolates animation parameters without resetting particle positions.

Heartbeats run every 5 seconds; missing updates for about 20 seconds mark a source disconnected. History restoration is bounded and runs independently of live events. A closed panel does not block agent tools.

## Main and subagent aggregation

Only main sessions get rows. A child's permission or question can turn its parent's light yellow; a child's completion cannot turn a still-running parent green. Recoverable child/tool errors do not automatically fail the main task. The main task's terminal error survives subsequent idle events.

Ordering uses the most recent task start. Merely browsing an older conversation does not move it to the top. Hover a row to see its full title, project and session ID.

## Compatibility

| Platform | Status |
| --- | --- |
| Ubuntu 22.04.5 / GNOME 42.9 / X11 / amd64 | ✅ Tested desktop target for v0.1.0 |
| Ubuntu 24.04 / GNOME / Wayland | ⚠️ Untested; validation planned |
| KDE Plasma | ⚠️ Untested |
| Mixed-DPI displays | ⚠️ Untested |
| macOS | ❌ Not supported in this release |
| Windows | ❌ Not supported in this release |

| Integration | Status |
| --- | --- |
| OpenCode terminal | ✅ Tested with 1.18.31 |
| `opencode serve` | ✅ Tested with 1.18.31, including authentication |
| OpenChamber | ✅ Tested with managed and external OpenCode servers |

Offscreen package tests do not imply Wayland compatibility. Python and PyQt5 are system dependencies; only the project's own code is covered by MIT.

## Privacy

SessionGlow communicates over localhost. **Prompt bodies, model responses, tool arguments and service credentials are not sent to the panel.** Snapshots contain session titles, IDs, parent relationships, project paths, states, timestamps and source diagnostics. A title can itself contain text chosen by you or OpenCode.

At initialization, the plugin queries a limited amount of recent OpenCode history and uses its message metadata to restore state. The panel stores at most 512 summaries in `~/.local/state/sessionglow/sessions.json`. There is no telemetry or automatic startup at login.

## Configuration

Use the tray/menu to set the session count, always-on-top and appearance. Configuration is stored at `~/.config/sessionglow/config.json`:

```json
{
  "max_sessions": 5,
  "fps": 30,
  "opacity": 0.97,
  "intensity": 0.85,
  "always_on_top": true,
  "position": null,
  "port": 8790
}
```

Restart the panel after manually editing this file. If the receiving port changes, also set `SESSIONGLOW_PORT` in OpenCode's startup environment.

<details>
<summary>Diagnostics and useful commands</summary>

```bash
sessionglow --version
sessionglow --install-plugin
sessionglow --demo --quit-after 15
sessionglow --render /tmp/sessionglow.png
curl -s http://127.0.0.1:8790/health | /usr/bin/python3 -m json.tool
```

`sources` identifies the actual OpenCode endpoint, PID and project. `connections` counts project plugin instances, not servers. If only terminal sessions appear, verify the OpenChamber backend and restart the correct process.

</details>

## Development and contributing

Source installation:

```bash
git clone https://github.com/YidaHao/SessionGlow.git
cd SessionGlow
sudo apt install python3-pyqt5
/usr/bin/python3 install.py
./run.sh
```

Contributions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for setup, tests, package builds, event debugging and platform validation. The [roadmap](https://github.com/YidaHao/SessionGlow/issues?q=is%3Aissue+label%3A%22help+wanted%22) tracks planned compatibility and packaging work.

| Documentation | Contents |
| --- | --- |
| [Installation](docs/INSTALL.md) | Packages, source setup, upgrades, removal and OpenChamber |
| [Usage (中文)](docs/USAGE.md) | Controls, ordering, appearance and troubleshooting |
| [Media](docs/assets/README.md) | Reproduce the short demo and Social Preview |
| [v0.1.0 release notes](docs/releases/v0.1.0.md) | Scope, compatibility and known limits |

[MIT License](LICENSE) · Copyright © 2026 YidaHao
