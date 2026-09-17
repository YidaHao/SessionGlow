"""Export a synthetic 20-second demo video; does not capture the desktop."""

import argparse
import os
import subprocess
import time
from unittest.mock import patch

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage
from PyQt5.QtWidgets import QApplication

from sessionglow.__main__ import DEFAULTS, demo_rows
from sessionglow.panel import Panel


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output")
    args = parser.parse_args()
    app = QApplication([])
    panel = Panel(dict(DEFAULTS), lambda: None, demo=True)
    panel.timer.stop()
    fps = 24
    width, height = panel.width(), panel.height()
    process = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pixel_format", "bgra",
                                "-video_size", f"{width}x{height}", "-framerate", str(fps), "-i", "-", "-an",
                                "-vf", "pad=ceil(iw/2)*2:ceil(ih/2)*2", "-c:v", "libvpx-vp9", "-crf", "30",
                                "-b:v", "0", "-deadline", "realtime", "-cpu-used", "5", args.output], stdin=subprocess.PIPE)
    origin = time.monotonic()
    panel.origin_time = origin
    try:
        for index in range(fps * 20):
            now = origin + index / fps
            with patch("sessionglow.panel.time.monotonic", return_value=now):
                panel.update_rows(demo_rows(index / fps), 1)
                for motion in panel.motions.values():
                    motion.advance(now)
                image = QImage(width, height, QImage.Format_ARGB32)
                image.fill(Qt.transparent)
                panel.render(image)
                process.stdin.write(image.bits().asstring(image.sizeInBytes()))
        process.stdin.close()
        assert process.wait(timeout=20) == 0
    finally:
        panel.tray.hide()
        if process.poll() is None:
            process.terminate()
            process.wait(timeout=3)
        app.quit()


if __name__ == "__main__":
    main()
