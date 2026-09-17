#!/usr/bin/python3
"""Render a 12-second synthetic permission lifecycle and a 1280x640 social card."""

import os
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

os.environ["QT_QPA_PLATFORM"] = "offscreen"
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from PyQt5.QtCore import QPointF, QRectF, Qt
from PyQt5.QtGui import QColor, QFont, QImage, QLinearGradient, QPainter, QPen
from PyQt5.QtSvg import QSvgRenderer
from PyQt5.QtWidgets import QApplication
from sessionglow.__main__ import DEFAULTS
from sessionglow.panel import LABELS, Panel


def face(size, bold=False):
    return QFont("DejaVu Sans", size, QFont.DemiBold if bold else QFont.Normal)


def scenario(t):
    state = "running" if t < 2.5 or 5 <= t < 8.5 else "waiting" if t < 5 else "done"
    return [{"id": f"demo-{index}", "title": title, "project": project, "state": status,
             "detail": "", "connected": True, "children": 0}
            for index, (title, project, status) in enumerate((
                ("Refactor the API", "api-service", state),
                ("Build search indexes", "search", "running"),
                ("Verify integration tests", "test-suite", "done"),
                ("Deploy preview", "preview", "failed"))) ]


class DemoPanel(Panel):
    caption = "Parallel tasks"

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor("#0e1724"))
        painter.setPen(QPen(QColor("#334b63"), 1))
        painter.drawRoundedRect(QRectF(8, 8, self.width() - 16, self.height() - 16), 16, 16)
        painter.setFont(face(13, True))
        painter.setPen(QColor("#e3effa"))
        painter.drawText(QPointF(28, 39), "SESSION / GLOW")
        painter.setFont(face(8))
        painter.setPen(QColor("#8fa6ba"))
        painter.drawText(QPointF(29, 59), "OPENCODE   /   LIVE SESSION LIGHTS")
        import time
        for index, row in enumerate(self.rows):
            self.draw_row(painter, row, self.HEADER + index * self.ROW, time.monotonic())
        painter.setFont(face(9))
        painter.setPen(QColor("#91b7ca"))
        painter.drawText(QRectF(28, self.height() - 38, 362, 24), Qt.AlignCenter, self.caption)
        painter.end()


def frame(panel, t):
    with patch("sessionglow.panel.time.monotonic", return_value=t):
        panel.update_rows(scenario(t), 1)
        for motion in panel.motions.values():
            motion.advance(t)
        panel.caption = ("Parallel tasks" if t < 2.5 else "Permission requested" if t < 4.5
                         else "Approved" if t < 5 else "Back to work" if t < 8.5 else "Task completed")
        image = QImage(panel.size(), QImage.Format_ARGB32)
        image.fill(QColor("#090f19"))
        panel.render(image)
        return image


def social(panel_image, path):
    image = QImage(1280, 640, QImage.Format_RGB32)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.Antialiasing)
    gradient = QLinearGradient(0, 0, 1280, 640)
    gradient.setColorAt(0, QColor("#0a1220"))
    gradient.setColorAt(1, QColor("#142e3e"))
    painter.fillRect(image.rect(), gradient)
    painter.setPen(QPen(QColor(79, 152, 186, 15), 1))
    for x in range(0, 1280, 48):
        painter.drawLine(x, 0, x, 640)
    for y in range(0, 640, 48):
        painter.drawLine(0, y, 1280, y)
    QSvgRenderer(str(ROOT / "icon.svg")).render(painter, QRectF(68, 64, 70, 70))
    painter.setPen(QColor("#e2edf6"))
    painter.setFont(face(35, True))
    painter.drawText(QPointF(156, 116), "SessionGlow")
    painter.setFont(face(25, True))
    painter.drawText(QPointF(74, 240), "Ambient status lights")
    painter.drawText(QPointF(74, 287), "for your OpenCode agents.")
    painter.setFont(face(17))
    painter.setPen(QColor("#95adbf"))
    painter.drawText(QPointF(75, 357), "See every OpenCode agent at a glance.")
    for index, (label, tint) in enumerate((("Working", "#55b6ff"), ("Needs you", "#f3bf49"),
                                          ("Done", "#3ddca7"), ("Failed", "#ff627b"))):
        x = 82 + index * 169
        painter.setBrush(QColor(tint))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPointF(x, 453), 5, 5)
        painter.setFont(face(13))
        painter.setPen(QColor("#bfd0df"))
        painter.drawText(QPointF(x + 15, 460), label)
    painter.setFont(face(12))
    painter.setPen(QColor("#738ca1"))
    painter.drawText(QPointF(75, 566), "LOCALHOST  /  EVENT-DRIVEN  /  UBUNTU + X11")
    painter.drawImage(QRectF(808, 69, 420, 488), panel_image)
    painter.end()
    if not image.save(str(path)):
        raise RuntimeError("Social Preview export failed")


def main():
    assets = ROOT / "docs/assets"
    assets.mkdir(parents=True, exist_ok=True)
    app = QApplication([])
    LABELS.update(unknown="Idle", running="Working", waiting="Needs you", failed="Failed", done="Done")
    panel = DemoPanel(dict(DEFAULTS, max_sessions=4), lambda: None, demo=True)
    panel.timer.stop()
    panel.origin_time = 0
    video = assets / "sessionglow-demo.webm"
    process = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pixel_format", "bgra",
                                "-video_size", f"{panel.width()}x{panel.height()}", "-framerate", "24", "-i", "-",
                                "-an", "-c:v", "libvpx-vp9", "-crf", "28", "-b:v", "0", "-deadline", "realtime",
                                "-cpu-used", "5", str(video)], stdin=subprocess.PIPE)
    try:
        for index in range(12 * 24):
            image = frame(panel, index / 24)
            if index == 84:
                social(image, assets / "social-preview.png")
            process.stdin.write(image.bits().asstring(image.sizeInBytes()))
        process.stdin.close()
        if process.wait(timeout=20):
            raise RuntimeError("Video export failed")
    finally:
        panel.tray.hide()
        if process.poll() is None:
            process.terminate()
            process.wait(timeout=3)
        app.quit()
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(video), "-filter_complex",
                    "[0:v]fps=12,split[f][c];[c]palettegen=max_colors=128:stats_mode=diff[p];"
                    "[f][p]paletteuse=dither=bayer:bayer_scale=3:diff_mode=rectangle",
                    "-loop", "0", str(assets / "sessionglow-demo.gif")], check=True)
    print("Rendered 12-second demo and 1280x640 Social Preview")


if __name__ == "__main__":
    main()
