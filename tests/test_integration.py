import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from sessionglow.integration import install_plugin, plugin_directory, uninstall_plugin


class IntegrationTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.source = self.root / "install with spaces"
        (self.source / "plugin").mkdir(parents=True)
        (self.source / "plugin/sessionglow.mjs").write_text("export default async () => ({ loaded: true });\n")
        self.plugins = self.root / "user-config/opencode/plugins"

    def test_install_idempotent_upgrade_and_remove(self):
        target, changed = install_plugin(self.source, self.plugins)
        self.assertTrue(changed)
        self.assertFalse(install_plugin(self.source, self.plugins)[1])
        self.assertIn("install%20with%20spaces", target.read_text())
        self.assertTrue(uninstall_plugin(self.plugins)[1])
        self.assertFalse(target.exists())
        self.assertFalse(uninstall_plugin(self.plugins)[1])

    def test_legacy_upgrade_preserves_other_plugins(self):
        self.plugins.mkdir(parents=True)
        other = self.plugins / "other.js"
        other.write_text("user code")
        target = self.plugins / "sessionglow.js"
        target.write_text('// Local session lights. Restart OpenCode after installation.\nexport { default } from "file:///old/plugin/sessionglow.mjs";\n')
        self.assertTrue(install_plugin(self.source, self.plugins)[1])
        self.assertEqual(other.read_text(), "user code")

    def test_does_not_overwrite_or_remove_user_plugin(self):
        self.plugins.mkdir(parents=True)
        target = self.plugins / "sessionglow.js"
        target.write_text("user code")
        for operation in (lambda: install_plugin(self.source, self.plugins), lambda: uninstall_plugin(self.plugins)):
            with self.assertRaises(ValueError):
                operation()
        self.assertEqual(target.read_text(), "user code")

    def test_removed_package_leaves_harmless_plugin_entry(self):
        target, _ = install_plugin(self.source, self.plugins)
        script = self.root / "entry.mjs"
        script.write_text(target.read_text())
        command = ["node", "--input-type=module", "-e",
                   "const {default: plugin} = await import(process.argv[1]); console.log(JSON.stringify(await plugin({})));", script.as_uri()]
        self.assertEqual(subprocess.check_output(command, text=True).strip(), '{"loaded":true}')
        (self.source / "plugin/sessionglow.mjs").unlink()
        self.assertEqual(subprocess.check_output(command, text=True).strip(), "{}")

    def test_honors_xdg_config_home(self):
        with patch.dict(os.environ, {"XDG_CONFIG_HOME": str(self.root / "custom")}):
            self.assertEqual(plugin_directory(), self.root / "custom/opencode/plugins")
