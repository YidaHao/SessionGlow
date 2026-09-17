#!/usr/bin/env bash
# Run in an isolated disposable Ubuntu container or CI runner as root.
set -euo pipefail
package="$(readlink -f "${1:?Usage: smoke_deb.sh path/to/package.deb}")"
version="$(dpkg-deb -f "$package" Version)"
test "$(id -u)" = 0
scratch="$(mktemp -d)"
trap 'rm -rf "$scratch"' EXIT
export DEBIAN_FRONTEND=noninteractive
export XDG_CONFIG_HOME="$scratch/config"
export QT_QPA_PLATFORM=offscreen
apt-get install -y --no-install-recommends python3
# A lower-version fixture uses the same payload to test dpkg's real upgrade path.
dpkg-deb --raw-extract "$package" "$scratch/previous"
/usr/bin/python3 -c 'from pathlib import Path; import sys; p=Path(sys.argv[1]); lines=p.read_text().splitlines(); p.write_text("\n".join("Version: 0.0.0" if line.startswith("Version:") else line for line in lines) + "\n")' "$scratch/previous/DEBIAN/control"
dpkg-deb --root-owner-group --build "$scratch/previous" "$scratch/sessionglow_0.0.0_amd64.deb"
apt-get install -y --no-install-recommends "$scratch/sessionglow_0.0.0_amd64.deb"
test "$(dpkg-query -W -f='${Version}' sessionglow)" = 0.0.0
apt-get install -y --no-install-recommends "$package"
test "$(dpkg-query -W -f='${Version}' sessionglow)" = "$version"
sessionglow --version
sessionglow --render "$scratch/preview.png"
test -s "$scratch/preview.png"
sessionglow --install-plugin
test -s "$XDG_CONFIG_HOME/opencode/plugins/sessionglow.js"
sessionglow --demo --quit-after 0.3
# Verify the package's automatic first-run integration under an isolated user config.
sessionglow --uninstall-plugin
sessionglow --port 0 --config "$scratch/settings.json" --cache "$scratch/history.json" --quit-after 0.5
test -s "$XDG_CONFIG_HOME/opencode/plugins/sessionglow.js"
# Reinstallation exercises replacement/upgrade of all packaged paths.
apt-get install -y --reinstall --no-install-recommends "$package"
sessionglow --install-plugin
sessionglow --uninstall-plugin
test ! -e "$XDG_CONFIG_HOME/opencode/plugins/sessionglow.js"
# System files stay root-owned, while an unprivileged desktop user can register.
chmod 755 "$scratch"
mkdir "$scratch/user-home"
chown nobody:nogroup "$scratch/user-home"
runuser -u nobody -- env HOME="$scratch/user-home" XDG_CONFIG_HOME="$scratch/user-home/.config" sessionglow --install-plugin
test -s "$scratch/user-home/.config/opencode/plugins/sessionglow.js"
runuser -u nobody -- env HOME="$scratch/user-home" XDG_CONFIG_HOME="$scratch/user-home/.config" sessionglow --uninstall-plugin
apt-get remove -y sessionglow
test ! -e /usr/bin/sessionglow
test ! -e /usr/share/sessionglow/plugin/sessionglow.mjs
test ! -e /usr/share/applications/sessionglow.desktop
printf '%s\n' 'PASS: package install, upgrade, render, first-run integration, reinstall, unregister and removal'
