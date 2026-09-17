#!/usr/bin/env bash
set -euo pipefail
if ! /usr/bin/python3 -c 'import PyQt5.QtWidgets' 2>/dev/null; then
    printf '%s\n' 'Install the desktop dependency: sudo apt install python3-pyqt5' >&2
    exit 1
fi
export PYTHONPATH="$(dirname "$(readlink -f "$0")")${PYTHONPATH:+:$PYTHONPATH}"
exec /usr/bin/python3 -m sessionglow "$@"
