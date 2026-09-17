<div align="center">

<img src="icon.svg" width="76" height="76" alt="SessionGlow logo" />

# SessionGlow

<p><a href="README.md">简体中文</a> · <strong>English</strong></p>

**A status light for every OpenCode session.**

A floating panel for the corner of your desktop.<br />
Interweaving currents, drifting particles, and flowing liquid show what your agents are doing.

<p>
  <img src="https://img.shields.io/badge/Ubuntu-22.04%20%7C%20X11-E95420?style=flat-square" alt="Tested on Ubuntu 22.04 / X11" />
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square" alt="Python 3.10 or later" />
  <img src="https://img.shields.io/badge/UI-PyQt5-41CD52?style=flat-square" alt="PyQt5 desktop interface" />
  <img src="https://img.shields.io/badge/OpenCode-Live%20events-55B6FF?style=flat-square" alt="Live OpenCode events" />
</p>

<p>
  <a href="#animation-preview">Animation preview</a> ·
  <a href="#quick-start">Quick start</a> ·
  <a href="docs/INSTALL.md">Installation guide (中文)</a> ·
  <a href="docs/USAGE.md">Usage guide (中文)</a>
</p>

</div>

---

## Animation preview

<p align="center">
  <img src="docs/assets/sessionglow-demo.gif" width="420" alt="SessionGlow animations: blue flowing currents, a red nearly stationary current, green flowing liquid, and jittery yellow currents. The fifth tube cycles through all four states." />
</p>

<p align="center">
  <sub>Rendered by the app · Synthetic demo sessions · The fifth tube changes state every 5 seconds</sub><br />
  <a href="docs/assets/sessionglow-demo.webm">Watch the 24 fps version</a>
</p>

### Four colors, four rhythms

| State | Inside the tube | What it means |
| :--- | :--- | :--- |
| 🔵 **Running** | Five currents weave gently through the tube, with particles following the currents and drifting freely inside | The agent is working or retrying automatically |
| 🔴 **Failed** | The currents settle into a nearly straight line; particles stop, leaving a slight tremor | The task has terminated and needs attention |
| 🟢 **Completed** | Currents and particles fade away as gently flowing green liquid fills the tube | This task has finished |
| 🟡 **Needs confirmation** | Full waveforms and particles move with more pronounced, irregular jitter | A permission request or question needs your response |

Each state change uses a **smooth transition of about 0.8 seconds**. Color, amplitude, particle motion, and liquid fill change together. If another update arrives mid-transition, the animation continues from its current appearance.

## Keep progress in view

| | |
| :--- | :--- |
| **One tube per main session**<br />Subagent activity and confirmation requests roll up into their parent session. | **Recent tasks, stable ordering**<br />Show 5 sessions by default, configurable from 1 to 12. Tool calls and heartbeats do not shuffle the list. |
| **Terminal and OpenChamber support**<br />Bring together sessions from local OpenCode servers and projects with the plugin installed. | **A movable floating panel**<br />Stay on top, remember your position, hide to the tray, and adjust opacity, frame rate, and effect intensity. |
| **Driven by real events**<br />Respond to task, error, permission, and question events without inferring activity from CPU usage. | **Local session history**<br />Keep recent summaries, mark disconnected sessions, and reconnect automatically when the panel opens again. |

All visual effects stay inside the panel. Respond to permissions and questions in OpenCode or OpenChamber.

## Quick start

The primary tested environment is **Ubuntu 22.04.5 + GNOME 42.9 + X11**, with **OpenCode 1.18.31**. Other desktops, Wayland window stacking, and mixed-DPI setups have not been verified.

### 1. Clone and install

```bash
git clone https://github.com/YidaHao/SessionGlow.git
cd SessionGlow

sudo apt install python3-pyqt5
/usr/bin/python3 install.py
```

The installer adds a global OpenCode plugin entry and an Ubuntu application launcher for your user. It preserves your existing `opencode.json`. The launcher uses the system Python, so no virtual environment is needed.

### 2. Open the panel

```bash
./run.sh
```

You can also search for **SessionGlow** in your application menu.

To preview all effects before connecting OpenCode:

```bash
./run.sh --demo
```

Demo mode works without OpenCode and displays all four states, plus a tube that cycles through them. The panel and demo currently use Chinese labels.

### 3. Restart the OpenCode instance you use

OpenCode loads plugins at startup. After installation, restart the terminal instance or server that runs your sessions.

| How you use OpenCode | How to connect |
| :--- | :--- |
| Directly in a terminal | Restart with `opencode -c` in your project directory to continue the most recent session |
| A standalone `opencode serve` process | Wait for tasks to finish, then restart that service with its original port and authentication settings |
| OpenChamber with a managed backend | Wait for tasks to finish, then run `openchamber restart --port 3000`, replacing the port with your actual web UI port |
| OpenChamber connected to an external OpenCode server | Restart the external OpenCode server; refreshing the browser does not reload its plugins |

**OpenChamber may use a backend port other than 4096.** It can launch its own server on a dynamically assigned port. See the [installation guide (Chinese)](docs/INSTALL.md) for both connection modes.

Once connected, start a task in OpenCode and its tube will light up.

## Everyday use

- **Move the panel:** drag the title bar. Its position is saved automatically.
- **Hide the panel:** click `−` in the upper-right corner. Event monitoring continues in the background.
- **Open the menu:** click `···` to adjust the session count, window stacking, and appearance. The appearance dialog is labeled `外观设置`.
- **Quit:** choose `退出 SessionGlow` from the tray menu. Agent tasks continue running.

Completed and failed sessions remain in the list. Increase the display count to keep more older sessions visible. Gray means no reliable task result is available. A lost connection is labeled `连接中断 · 上次状态` (disconnected · last known state), rather than being treated as task completion.

<details>
<summary><strong>Configuration and common options</strong></summary>

Adjust appearance from the menu, or edit `~/.config/sessionglow/config.json`:

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

Restart the panel after editing the file manually. A lower frame rate reduces rendering work; lower intensity makes the effects more subtle. Rendering stops while the panel is hidden.

```bash
# Use a custom configuration
./run.sh --config /path/to/config.json

# Run the demo for 15 seconds
./run.sh --demo --quit-after 15

# Export a synthetic preview image
./run.sh --render /tmp/sessionglow.png
```

</details>

<details>
<summary><strong>Check your connection and server sources</strong></summary>

```bash
curl -s http://127.0.0.1:8790/health | /usr/bin/python3 -m json.tool
```

`sources` lists actual OpenCode server addresses, process IDs, and project directories. `sessions` lists the sessions shown in the panel. One server can initialize several projects, so `connections` is not the number of servers or sessions.

If terminal sessions appear but OpenChamber sessions do not, check the actual backend port and where the plugin was loaded. More troubleshooting steps are available in the [usage guide (Chinese)](docs/USAGE.md#排查终端会话可见openchamber-会话不可见).

</details>

## Local, on-demand monitoring

The plugin sends session titles, directories, states, timestamps, and other diagnostic metadata to `127.0.0.1:8790` on your machine. **It does not send prompt bodies, response bodies, tool arguments, or server passwords to the panel.** At startup, it queries a limited amount of recent history through the OpenCode API to restore session summaries. Live events do not wait for this history to load.

Summaries are stored in `~/.local/state/sessionglow/sessions.json`. Closing the panel does not block OpenCode, and heartbeats restore the connection when it reopens. Startup at login is not enabled by default.

## Documentation and development

The detailed guides below are currently available in Chinese.

| Guide | Contents |
| :--- | :--- |
| [Installation and integration](docs/INSTALL.md) | Install, upgrade, uninstall, terminal and server setup, and both OpenChamber modes |
| [Usage and troubleshooting](docs/USAGE.md) | Tube states, session ordering, appearance settings, and connection diagnostics |
| [Generating demo assets](docs/assets/README.md) | Reproduce the README GIF and the higher-frame-rate video |

Run the automated tests:

```bash
/usr/bin/python3 -m unittest discover -s tests -p 'test_*.py' -v
node --test tests/plugin.test.mjs
```

With the plugin installed and the panel running, verify real OpenCode sessions:

```bash
/usr/bin/python3 tests/live_opencode.py
```

This creates temporary sessions and runs short local commands to check parent/child aggregation, ordering, and state changes. It does not call a model. See the [usage guide](docs/USAGE.md) and [tests directory](tests/) for desktop interaction checks and other commands.

---

<p align="center">
  <sub>A glance at progress, then back to what you were doing.</sub>
</p>
