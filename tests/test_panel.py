import os
import time
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication

from sessionglow.__main__ import DEFAULTS, demo_rows
from sessionglow.panel import Panel


class PanelTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.panel = Panel(dict(DEFAULTS), lambda: None, demo=True)
        self.panel.timer.stop()
        self.addCleanup(self.panel.tray.hide)
        self.addCleanup(self.panel.hide)

    def render(self):
        image = QImage(self.panel.size(), QImage.Format_ARGB32_Premultiplied)
        image.fill(Qt.transparent)
        self.panel.render(image)
        return image

    def test_each_color_rendered_and_all_animations_change_over_time(self):
        self.panel.update_rows(demo_rows(), 1)
        now = time.monotonic()
        for motion in self.panel.motions.values():
            motion.since = now - 1
        first = self.render()
        for index, channel in ((0, "blue"), (1, "red"), (2, "green")):
            sample = first.pixelColor(201, self.panel.HEADER + index * self.panel.ROW + 48)
            channels = {"red": sample.red(), "green": sample.green(), "blue": sample.blue()}
            self.assertEqual(max(channels, key=channels.get), channel)
        QTest.qWait(160)
        for motion in self.panel.motions.values():
            motion.advance(time.monotonic())
        second = self.render()
        for index in range(4):
            area = (38, self.panel.HEADER + index * self.panel.ROW + 35, 344, 26)
            self.assertNotEqual(first.copy(*area), second.copy(*area), f"State {index} should animate")

    def test_new_row_order_reuses_motion_and_moves_continuously(self):
        rows = demo_rows()
        self.panel.update_rows(rows, 1)
        motion = self.panel.motions["demo-0"]
        previous_y = self.panel.positions["demo-0"]
        self.panel.update_rows(rows[1:] + rows[:1], 1)
        self.assertIs(self.panel.motions["demo-0"], motion)
        self.assertEqual(self.panel.positions["demo-0"], previous_y)
        self.panel.set_count(3)
        self.assertEqual(self.panel.height(), self.panel.HEADER + 3 * self.panel.ROW + 48)


if __name__ == "__main__":
    unittest.main()
