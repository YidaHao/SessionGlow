#!/usr/bin/python3
"""Build the Ubuntu amd64 release using only Python and dpkg-deb."""

import argparse
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from sessionglow import __version__


def build(output):
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="sessionglow-deb-") as temporary:
        stage = Path(temporary)
        app = stage / "usr/share/sessionglow"
        app.mkdir(parents=True)
        for directory in ("sessionglow", "plugin"):
            shutil.copytree(ROOT / directory, app / directory,
                            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        (app / "PACKAGED").write_text(__version__ + "\n")
        files = {
            "packaging/sessionglow": "usr/bin/sessionglow",
            "packaging/sessionglow.desktop": "usr/share/applications/sessionglow.desktop",
            "icon.svg": "usr/share/icons/hicolor/scalable/apps/sessionglow.svg",
            "LICENSE": "usr/share/doc/sessionglow/copyright",
            "docs/INSTALL.md": "usr/share/doc/sessionglow/INSTALL.md",
            "docs/USAGE.md": "usr/share/doc/sessionglow/USAGE.md",
        }
        for source, destination in files.items():
            target = stage / destination
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / source, target)
        size = sum(p.stat().st_size for p in stage.rglob("*") if p.is_file())
        control = stage / "DEBIAN"
        control.mkdir()
        (control / "control").write_text(f"""Package: sessionglow
Version: {__version__}
Section: devel
Priority: optional
Architecture: amd64
Maintainer: YidaHao <YidaHao@users.noreply.github.com>
Depends: python3 (>= 3.10), python3-pyqt5 (>= 5.15)
Recommends: fonts-noto-cjk
Installed-Size: {(size + 1023) // 1024}
Homepage: https://github.com/YidaHao/SessionGlow
Description: Ambient status lights for your OpenCode agents
 A floating Qt panel for OpenCode session activity, completion, failure,
 and confirmation requests. Tested on Ubuntu 22.04, GNOME and X11.
""")
        # Fixed metadata makes identical source inputs produce identical bytes.
        epoch = int(os.environ.get("SOURCE_DATE_EPOCH", "0"))
        for path in sorted(stage.rglob("*"), reverse=True):
            path.chmod(0o755 if path.is_dir() or path == stage / "usr/bin/sessionglow" else 0o644)
            os.utime(path, (epoch, epoch))
        stage.chmod(0o755)
        os.utime(stage, (epoch, epoch))
        name = f"sessionglow_{__version__}_amd64.deb"
        target = output / name
        subprocess.run(["dpkg-deb", "--root-owner-group", "-Zxz", "--build", str(stage), str(target)],
                       check=True, env=dict(os.environ, SOURCE_DATE_EPOCH=str(epoch)))
        checksum = hashlib.sha256(target.read_bytes()).hexdigest()
        (output / "SHA256SUMS").write_text(f"{checksum}  {name}\n")
        print(f"Built {target} ({target.stat().st_size:,} bytes)")
    return target


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "dist")
    build(parser.parse_args().output.resolve())
