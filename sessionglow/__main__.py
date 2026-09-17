import argparse
import json
import os
import queue
import signal
import sys
import time
from pathlib import Path

from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QImage
from PyQt5.QtWidgets import QApplication

from . import __version__
from .integration import install_plugin, uninstall_plugin
from .model import SessionStore
from .panel import Panel
from .server import Server


DEFAULTS = {"max_sessions": 5, "fps": 30, "opacity": 0.97, "intensity": 0.85,
            "always_on_top": True, "position": None, "port": 8790}


def load_settings(path):
    values = dict(DEFAULTS)
    if path.exists():
        raw = json.loads(path.read_text())
        if not isinstance(raw, dict):
            raise ValueError("Configuration must be a JSON object")
        values.update({key: raw[key] for key in DEFAULTS if key in raw})
    for key, low, high in (("max_sessions", 1, 12), ("fps", 10, 60), ("port", 0, 65535)):
        if type(values[key]) is not int or not low <= values[key] <= high:
            raise ValueError(f"{key} must be an integer between {low} and {high}")
    for key, low, high in (("opacity", 0.65, 1), ("intensity", 0.2, 1.2)):
        if type(values[key]) not in (float, int) or not low <= values[key] <= high:
            raise ValueError(f"{key} must be between {low} and {high}")
    if type(values["always_on_top"]) is not bool:
        raise ValueError("always_on_top must be a boolean")
    return values


def demo_rows(elapsed=0):
    states = ("running", "failed", "done", "waiting", ("running", "waiting", "failed", "done")[int(elapsed / 5) % 4])
    titles = ("构建检索服务与索引", "修复部署流水线", "完成 API 集成测试", "等待数据库迁移确认", "状态切换 · 连续过渡")
    return [{"id": f"demo-{i}", "title": title, "project": f"~/Workspace/{project}",
             "state": state, "detail": detail, "connected": True, "children": 0, "last_started": 5 - i}
            for i, (state, title, project, detail) in enumerate(zip(states, titles,
                ("SearchEngine", "Deployment", "Backend", "Database", "SessionGlow"),
                ("", "APIError", "", "等待授权", "每 5 秒切换一次")))]


def main():
    parser = argparse.ArgumentParser(description="SessionGlow · floating OpenCode session lights")
    parser.add_argument("--version", action="version", version=f"SessionGlow {__version__}")
    integration = parser.add_mutually_exclusive_group()
    integration.add_argument("--install-plugin", action="store_true", help="Register the plugin for the current user and exit")
    integration.add_argument("--uninstall-plugin", action="store_true", help="Remove the current user's managed plugin and exit")
    parser.add_argument("--no-plugin-install", action="store_true", help="Skip packaged first-run plugin registration")
    parser.add_argument("--demo", action="store_true", help="Show four states and a continuously transitioning fifth tube")
    parser.add_argument("--port", type=int, help="Loopback event receiver port (default 8790)")
    parser.add_argument("--config", type=Path, default=Path.home() / ".config/sessionglow/config.json")
    parser.add_argument("--cache", type=Path, default=Path.home() / ".local/state/sessionglow/sessions.json")
    parser.add_argument("--render", type=Path, help="Render only synthetic demo data to a PNG, then exit")
    parser.add_argument("--quit-after", type=float, help="Exit automatically after N seconds")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    if args.install_plugin or args.uninstall_plugin:
        try:
            target, changed = uninstall_plugin() if args.uninstall_plugin else install_plugin(root)
        except (ValueError, OSError) as exc:
            parser.exit(1, f"SessionGlow: {exc}\n")
        print(f"{'Updated' if changed else 'No change'}: {target}. Restart OpenCode to apply.")
        return 0
    if args.render:
        os.environ["QT_QPA_PLATFORM"] = "offscreen"
    try:
        settings = load_settings(args.config)
        if args.port is not None:
            if not 0 <= args.port <= 65535:
                raise ValueError("--port must be between 0 and 65535")
            settings["port"] = args.port
    except (OSError, ValueError) as exc:
        parser.exit(1, f"SessionGlow: {exc}\n")
    app = QApplication([sys.argv[0]])
    app.setApplicationName("SessionGlow")
    app.setQuitOnLastWindowClosed(False)

    def save_settings():
        if args.demo or args.render:
            return
        try:
            args.config.parent.mkdir(parents=True, exist_ok=True)
            temp = args.config.with_suffix(".tmp")
            temp.write_text(json.dumps(settings, ensure_ascii=False, indent=2))
            temp.replace(args.config)
        except OSError as exc:
            print(f"SessionGlow: could not save settings: {exc}", file=sys.stderr)

    panel = Panel(settings, save_settings, demo=args.demo or bool(args.render))
    if args.render:
        panel.update_rows(demo_rows(), 1)
        now = time.monotonic()
        for motion in panel.motions.values():
            motion.since = now - 1
            motion.phase = 1
        image = QImage(panel.size() * 2, QImage.Format_ARGB32_Premultiplied)
        image.setDevicePixelRatio(2)
        image.fill(Qt.transparent)
        panel.render(image)
        success = image.save(str(args.render))
        panel.tray.hide()
        return 0 if success else 1
    try:
        server = Server(settings["port"]) if not args.demo else None
    except OSError as exc:
        panel.tray.hide()
        parser.exit(1, f"SessionGlow: {exc}. An instance may already be running.\n")
    if (root / "PACKAGED").exists() and not args.demo and not args.no_plugin_install:
        try:
            target, changed = install_plugin(root)
            if changed:
                panel.tray.showMessage("SessionGlow", "OpenCode plugin installed. Restart OpenCode to connect.")
                print(f"SessionGlow: installed {target}; restart OpenCode to connect", flush=True)
        except (ValueError, OSError) as exc:
            panel.tray.showMessage("SessionGlow", str(exc))
            print(f"SessionGlow: {exc}", file=sys.stderr)
    store = SessionStore(args.cache) if not args.demo else None
    start = time.monotonic()
    last_save = start

    def tick():
        nonlocal last_save
        now = time.monotonic()
        if args.demo:
            panel.update_rows(demo_rows(now - start)[:settings["max_sessions"]], 0)
            return
        for _ in range(64):
            try:
                body = server.events.get_nowait()
            except queue.Empty:
                break
            store.receive(body, now)
        rows = store.rows(settings["max_sessions"], now)
        count = store.connection_count(now)
        panel.update_rows(rows, count)
        server.snapshot = {"app": "SessionGlow", "connections": count, "sessions": rows,
                           "visible": panel.isVisible(), "max_sessions": settings["max_sessions"],
                           "sources": store.sources(now)}
        if now - last_save >= 2:
            last_save = now
            try:
                store.save()
            except OSError as exc:
                print(f"SessionGlow: could not save session history: {exc}", file=sys.stderr)

    timer = QTimer()
    timer.timeout.connect(tick)
    timer.start(100)
    if server:
        server.start()
    tick()
    panel.show()

    def cleanup():
        timer.stop()
        panel.timer.stop()
        panel.tray.hide()
        if server:
            server.close()
            try:
                store.save()
            except OSError:
                pass

    app.aboutToQuit.connect(cleanup)
    signal.signal(signal.SIGINT, lambda *_: app.quit())
    signal.signal(signal.SIGTERM, lambda *_: app.quit())
    if args.quit_after is not None:
        QTimer.singleShot(max(1, round(args.quit_after * 1000)), app.quit)
    print(f"SessionGlow: {'demo' if args.demo else 'http://127.0.0.1:' + str(server.port)}", flush=True)
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
