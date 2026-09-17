#!/usr/bin/python3
"""Install per-user launcher/plugin without editing opencode.json."""

import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--replace-windowrag", action="store_true", help="Disable the previous WindowRag plugin entry")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    plugins = Path.home() / ".config/opencode/plugins"
    launcher = Path.home() / ".local/share/applications/sessionglow.desktop"
    target = plugins / "sessionglow.js"
    content = f"// Local session lights. Restart OpenCode after installation.\nexport {{ default }} from {json.dumps((root / 'plugin/sessionglow.mjs').as_uri())};\n"
    if target.exists() and target.read_text() != content:
        parser.exit(1, f"Existing plugin differs; inspect it first: {target}\n")
    old = plugins / "windowrag.js"
    backup = plugins / "windowrag.js.disabled"
    if args.replace_windowrag and old.exists():
        if backup.exists() or "WindowRag/linux/opencode-plugin.mjs" not in old.read_text():
            parser.exit(1, "Cannot safely back up the existing WindowRag plugin; inspect it first.\n")
    plugins.mkdir(parents=True, exist_ok=True)
    launcher.parent.mkdir(parents=True, exist_ok=True)
    if args.replace_windowrag and old.exists():
        old.rename(backup)
    target.write_text(content)
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
