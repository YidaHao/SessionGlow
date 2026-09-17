"""Exercise our own panel on a real X11 desktop; restore pointer and focus."""

import os
import subprocess
import time

from PyQt5.QtCore import QPoint, Qt
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication

from sessionglow.__main__ import DEFAULTS, demo_rows
from sessionglow.panel import Panel


def main():
    if os.environ.get("XDG_SESSION_TYPE") != "x11":
        raise SystemExit("This test requires an X11 desktop")
    app = QApplication([])
    app.setQuitOnLastWindowClosed(False)
    saved = []
    settings = dict(DEFAULTS)
    panel = Panel(settings, lambda: saved.append(dict(settings)), demo=True)
    panel.update_rows(demo_rows(), 1)
    old_pointer = subprocess.check_output(["xdotool", "getmouselocation", "--shell"], text=True)
    coordinates = dict(line.split("=", 1) for line in old_pointer.splitlines())
    old_focus = subprocess.check_output(["xdotool", "getactivewindow"], text=True).strip()
    def pump(seconds=0.2):
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            app.processEvents()
            time.sleep(0.01)
    try:
        panel.show()
        pump()
        flags = subprocess.check_output(["xprop", "-id", str(int(panel.winId())), "_NET_WM_STATE"], text=True)
        assert "_NET_WM_STATE_ABOVE" in flags, flags
        before = panel.pos()
        QTest.mousePress(panel, Qt.LeftButton, pos=QPoint(120, 35))
        pump(0.05)
        QTest.mouseMove(panel, QPoint(160, 65), delay=40)
        pump(0.15)
        QTest.mouseRelease(panel, Qt.LeftButton, pos=QPoint(160, 65))
        pump()
        assert panel.pos() != before, "Header did not drag the window"
        assert saved and settings["position"] == [panel.x(), panel.y()]
        panel.set_count(3)
        pump()
        assert panel.height() == panel.HEADER + panel.ROW * 3 + 48
        QTest.mouseClick(panel, Qt.LeftButton, pos=QPoint(381, 31))
        pump()
        assert not panel.isVisible(), "Minimize control did not hide the panel"
        panel.toggle()
        pump()
        assert panel.isVisible()
        print("PASS: real X11 topmost window, header dragging, position persistence, row count, hide/show")
    finally:
        panel.timer.stop()
        panel.tray.hide()
        panel.hide()
        subprocess.run(["xdotool", "mousemove", coordinates["X"], coordinates["Y"]], check=True)
        subprocess.run(["xdotool", "windowactivate", old_focus], check=False, stderr=subprocess.DEVNULL)


if __name__ == "__main__":
    main()
