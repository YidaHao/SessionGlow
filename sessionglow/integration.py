"""Per-user OpenCode integration shared by source and packaged installations."""

import json
import os
from pathlib import Path


MARKER = "// Managed by SessionGlow."
LEGACY = "// Local session lights. Restart OpenCode after installation."


def plugin_directory():
    root = Path(os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config")))
    return root / "opencode/plugins"


def managed(content):
    return content.startswith(MARKER + "\n") or (
        content.startswith(LEGACY + "\n") and "/plugin/sessionglow.mjs" in content)


def plugin_entry(root):
    url = json.dumps((Path(root).resolve() / "plugin/sessionglow.mjs").as_uri())
    # After apt remove, the user-owned entry remains harmless until removed.
    return f'''{MARKER}
// Restart OpenCode after installation, upgrade or removal.
import {{ existsSync }} from "node:fs";
import {{ fileURLToPath }} from "node:url";
const source = {url};
export default async function SessionGlowEntry(input) {{
  if (!existsSync(fileURLToPath(source))) return {{}};
  const {{ default: plugin }} = await import(source);
  return plugin(input);
}}
'''


def install_plugin(root, directory=None):
    root = Path(root).resolve()
    if not (root / "plugin/sessionglow.mjs").is_file():
        raise ValueError(f"Plugin source is missing: {root}")
    target = Path(directory or plugin_directory()) / "sessionglow.js"
    if target.is_symlink():
        raise ValueError(f"Existing plugin is a symlink; inspect it before replacing: {target}")
    content = plugin_entry(root)
    if target.exists():
        old = target.read_text()
        if old == content:
            return target, False
        if not managed(old):
            raise ValueError(f"Existing plugin is not managed by SessionGlow: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    temp = target.with_suffix(".tmp")
    temp.write_text(content)
    temp.replace(target)
    return target, True


def uninstall_plugin(directory=None):
    target = Path(directory or plugin_directory()) / "sessionglow.js"
    if target.is_symlink():
        raise ValueError(f"Existing plugin is a symlink; remove it manually after inspection: {target}")
    if not target.exists():
        return target, False
    if not managed(target.read_text()):
        raise ValueError(f"Refusing to remove an unrelated plugin: {target}")
    target.unlink()
    return target, True
