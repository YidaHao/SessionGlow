#!/usr/bin/python3
"""Install per-user launcher/plugin without editing opencode.json."""

import argparse
from pathlib import Path

from sessionglow.integration import install_plugin, plugin_directory, uninstall_plugin


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--replace-windowrag", action="store_true", help="Disable the previous WindowRag plugin entry")
    parser.add_argument("--uninstall", action="store_true", help="Remove this user's plugin and source launcher")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    plugins = plugin_directory()
    launcher = Path.home() / ".local/share/applications/sessionglow.desktop"
    if args.uninstall:
        try:
            target, removed = uninstall_plugin()
        except (ValueError, OSError) as exc:
            parser.exit(1, f"{exc}\n")
        if launcher.exists() and f'Exec="{root / "run.sh"}"' in launcher.read_text():
            launcher.unlink()
        print(f"Plugin {'removed' if removed else 'already absent'}: {target}")
        print("Restart OpenCode. Your settings and session history are preserved.")
        return
    old = plugins / "windowrag.js"
    backup = plugins / "windowrag.js.disabled"
    if args.replace_windowrag and old.exists():
        if backup.exists() or "WindowRag/linux/opencode-plugin.mjs" not in old.read_text():
            parser.exit(1, "Cannot safely back up the existing WindowRag plugin; inspect it first.\n")
    try:
        target, _ = install_plugin(root)
    except (ValueError, OSError) as exc:
        parser.exit(1, f"{exc}\n")
    launcher.parent.mkdir(parents=True, exist_ok=True)
    if args.replace_windowrag and old.exists():
        old.rename(backup)
    launcher.write_text(f'''[Desktop Entry]
Type=Application
Name=SessionGlow
Comment=OpenCode session status lights
Exec="{root / 'run.sh'}"
Path={root}
Icon={root / 'icon.svg'}
Terminal=false
Categories=Development;
StartupWMClass=SessionGlow
''')
    print(f"Installed plugin: {target}")
    print(f"Installed launcher: {launcher}")
    print("Restart OpenCode to load the plugin. Start the panel with ./run.sh or your applications menu.")


if __name__ == "__main__":
    main()
