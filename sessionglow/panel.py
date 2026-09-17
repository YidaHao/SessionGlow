"""Compact Qt panel: all light stays inside the floating window."""

import math
import time
from pathlib import Path

from PyQt5.QtCore import QPointF, QRectF, Qt, QTimer
from PyQt5.QtGui import (QColor, QFont, QIcon, QLinearGradient, QPainter,
                         QPainterPath, QPen, QPixmap, QRadialGradient)
from PyQt5.QtWidgets import (QActionGroup, QApplication, QDialog, QDialogButtonBox,
                             QFormLayout, QMenu, QSlider, QSpinBox, QSystemTrayIcon, QWidget)

from .motion import Motion, wave


LABELS = {"unknown": "待机", "running": "进行中", "failed": "任务失败", "done": "已完成", "waiting": "待确认"}


def color(rgb, alpha=255):
    return QColor(*(round(max(0, min(255, v))) for v in rgb[:3]), round(max(0, min(255, alpha))))

def font(size, weight=QFont.Normal):
    result = QFont("Noto Sans CJK SC", size)
    result.setWeight(weight)
    return result


class Panel(QWidget):
    HEADER = 76
    ROW = 91

    def __init__(self, settings, save_settings, demo=False):
        super().__init__(None, Qt.Tool | Qt.FramelessWindowHint)
        self.settings, self.save_settings = settings, save_settings
        self.demo = demo
        self.rows = []
        self.motions = {}
        self.connections = 0
        self.origin_time = time.monotonic()
        self.drag = None
        self.positions = {}
        self.setWindowTitle("SessionGlow")
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setMouseTracking(True)
        self.setWindowFlag(Qt.WindowStaysOnTopHint, settings["always_on_top"])
        self.resize(420, self.HEADER + settings["max_sessions"] * self.ROW + 48)
        self.restore_position()
        self.make_tray()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.frame)
        self.timer.start(round(1000 / settings["fps"]))

    def restore_position(self):
        available = QApplication.primaryScreen().availableGeometry()
        point = self.settings.get("position")
        if isinstance(point, list) and len(point) == 2 and all(type(v) is int for v in point):
            candidate = QPointF(*point).toPoint()
            if any(s.availableGeometry().contains(candidate) for s in QApplication.screens()):
                self.move(candidate)
                return
        self.move(available.right() - self.width() - 24, available.top() + 64)

    def make_tray(self):
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(QColor("#74c9ff"), 2))
        painter.setBrush(QColor("#101b2e"))
        painter.drawRoundedRect(QRectF(3, 9, 26, 14), 6, 6)
        painter.drawLine(8, 16, 24, 16)
        painter.end()
        self.setWindowIcon(QIcon(pixmap))
        self.tray = QSystemTrayIcon(QIcon(pixmap), self)
        self.tray.setToolTip("SessionGlow · OpenCode 会话状态")
        self.menu = QMenu()
        self.menu.addAction("显示 / 隐藏面板", self.toggle)
        self.top_action = self.menu.addAction("始终置顶")
        self.top_action.setCheckable(True)
        self.top_action.setChecked(self.settings["always_on_top"])
        self.top_action.toggled.connect(self.set_top)
        counts = self.menu.addMenu("显示会话数")
        group = QActionGroup(self)
        for count in (3, 5, 7, 10):
            action = counts.addAction(str(count))
            action.setCheckable(True)
            action.setChecked(count == self.settings["max_sessions"])
            group.addAction(action)
            action.triggered.connect(lambda _, n=count: self.set_count(n))
        self.menu.addAction("外观设置…", self.preferences)
        self.menu.addSeparator()
        self.menu.addAction("退出 SessionGlow", QApplication.instance().quit)
        self.tray.setContextMenu(self.menu)
        self.tray.activated.connect(lambda reason: self.toggle() if reason == QSystemTrayIcon.Trigger else None)
        if QApplication.platformName() != "offscreen":
            self.tray.show()

    def preferences(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("SessionGlow 外观")
        form = QFormLayout(dialog)
        count = QSpinBox()
        count.setRange(1, 12)
        count.setValue(self.settings["max_sessions"])
        fps = QSpinBox()
        fps.setRange(10, 60)
        fps.setValue(self.settings["fps"])
        opacity = QSlider(Qt.Horizontal)
        opacity.setRange(65, 100)
        opacity.setValue(round(self.settings["opacity"] * 100))
        intensity = QSlider(Qt.Horizontal)
        intensity.setRange(20, 120)
        intensity.setValue(round(self.settings["intensity"] * 100))
        for label, widget in (("会话数量", count), ("动画帧率", fps), ("面板不透明度", opacity), ("动效强度", intensity)):
            form.addRow(label, widget)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        form.addRow(buttons)
        if dialog.exec_():
            self.settings.update(fps=fps.value(), opacity=opacity.value() / 100, intensity=intensity.value() / 100)
            self.set_count(count.value())
            self.timer.setInterval(round(1000 / self.settings["fps"]))

    def set_top(self, enabled):
        self.settings["always_on_top"] = enabled
        visible = self.isVisible()
        self.setWindowFlag(Qt.WindowStaysOnTopHint, enabled)
        if visible:
            self.show()
        self.save_settings()

    def set_count(self, count):
        self.settings["max_sessions"] = count
        self.resize(420, self.HEADER + count * self.ROW + 48)
        self.save_settings()
        self.update()

    def toggle(self):
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self.raise_()

    def showEvent(self, event):
        # Reopening the panel must not integrate all the time spent hidden.
        now = time.monotonic()
        for motion in self.motions.values():
            motion.last = now
        super().showEvent(event)

    def closeEvent(self, event):
        self.hide()
        event.ignore()

    def update_rows(self, rows, connections):
        if rows == self.rows and connections == self.connections:
            return
        self.rows, self.connections = rows, connections
        now = time.monotonic()
        for index, row in enumerate(rows):
            if row["id"] not in self.motions:
                self.motions[row["id"]] = Motion(now)
                self.positions[row["id"]] = self.HEADER + index * self.ROW
            self.motions[row["id"]].change(row["state"], now)
        retained = {r["id"] for r in rows}
        self.motions = {key: value for key, value in self.motions.items() if key in retained}
        self.positions = {key: value for key, value in self.positions.items() if key in retained}
        if self.isVisible():
            self.update()

    def frame(self):
        if not self.isVisible() or not self.rows:
            return
        now = time.monotonic()
        for index, row in enumerate(self.rows):
            motion = self.motions[row["id"]]
            dt = max(0, min(0.1, now - motion.last))
            motion.advance(now)
            y = self.positions[row["id"]]
            self.positions[row["id"]] = y + (self.HEADER + index * self.ROW - y) * (1 - math.exp(-dt * 12))
        self.update()

    def paintEvent(self, _):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        panel = QRectF(8, 8, self.width() - 16, self.height() - 16)
        painter.setPen(Qt.NoPen)
        for spread in range(7, 0, -1):
            painter.setBrush(QColor(0, 0, 0, 5))
            painter.drawRoundedRect(panel.adjusted(-spread, -spread / 2, spread, spread), 17, 17)
        background = QLinearGradient(panel.topLeft(), panel.bottomRight())
        alpha = round(self.settings["opacity"] * 255)
        background.setColorAt(0, QColor(18, 25, 38, alpha))
        background.setColorAt(1, QColor(9, 14, 24, alpha))
        painter.setBrush(background)
        painter.setPen(QPen(QColor(103, 147, 177, 65), 1))
        painter.drawRoundedRect(panel, 14, 14)
        painter.setPen(QPen(QColor(97, 183, 219, 85), 1))
        painter.drawLine(29, 9, 103, 9)
        painter.setFont(font(12, QFont.DemiBold))
        painter.setPen(QColor("#e0e9f1"))
        painter.drawText(QRectF(26, 19, 245, 25), "SESSION / GLOW")
        painter.setFont(font(8))
        painter.setPen(QColor("#7c8c9f"))
        subtitle = "动效预览 · 状态循环" if self.demo else "OPENCODE   /   最近发起的任务"
        painter.drawText(QRectF(27, 44, 300, 20), subtitle)
        painter.setFont(font(13))
        painter.setPen(QColor("#8496aa"))
        painter.drawText(QRectF(337, 21, 25, 25), Qt.AlignCenter, "···")
        painter.drawText(QRectF(369, 21, 25, 25), Qt.AlignCenter, "−")
        now = time.monotonic()
        for index in range(self.settings["max_sessions"]):
            if index < len(self.rows):
                row = self.rows[index]
                y = self.positions[row["id"]]
                self.draw_row(painter, row, y, now)
            else:
                self.draw_empty(painter, index, self.HEADER + index * self.ROW)
        footer_y = self.height() - 34
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#50cea9" if self.connections else "#64748b"))
        painter.drawEllipse(QPointF(29, footer_y + 5), 2.5, 2.5)
        painter.setFont(font(8))
        painter.setPen(QColor("#8b9caf"))
        text = f"{self.connections} 个连接" if self.connections else "等待 OpenCode 连接"
        if self.demo:
            text = "演示数据"
        painter.drawText(QRectF(39, footer_y - 5, 225, 19), text)
        painter.setPen(QColor("#546579"))
        painter.drawText(QRectF(269, footer_y - 5, 120, 19), Qt.AlignRight, f"{len(self.rows):02d} / {self.settings['max_sessions']:02d}")
        painter.end()

    def draw_empty(self, painter, index, y):
        painter.setPen(QPen(QColor(97, 134, 160, 28), 1, Qt.DashLine))
        painter.setBrush(QColor(8, 13, 21, 30))
        painter.drawRoundedRect(QRectF(23, y, self.width() - 46, self.ROW - 10), 8, 8)
        painter.setFont(font(9))
        painter.setPen(QColor("#425369"))
        painter.drawText(QRectF(38, y + 24, 330, 24), Qt.AlignCenter,
                         "发起一个 OpenCode 任务，让灯管亮起" if index == 0 else "等待会话")

    def draw_row(self, painter, row, y, now):
        motion = self.motions[row["id"]]
        values = motion.values(now)
        rgb = values[:3]
        painter.save()
        painter.setBrush(QColor(6, 12, 21, 95))
        painter.setPen(QPen(color(rgb, 24), 1))
        painter.drawRoundedRect(QRectF(23, y, self.width() - 46, self.ROW - 10), 8, 8)
        painter.setFont(font(10, QFont.Medium))
        title = painter.fontMetrics().elidedText(row["title"], Qt.ElideRight, 249)
        painter.setPen(QColor("#d3dee9"))
        painter.drawText(QRectF(37, y + 7, 250, 22), Qt.AlignVCenter, title)
        painter.setFont(font(8))
        painter.setPen(color(rgb, 225))
        painter.drawText(QRectF(289, y + 8, 91, 20), Qt.AlignRight | Qt.AlignVCenter, LABELS[row["state"]])
        tube = QRectF(38, y + 35, self.width() - 76, 26)
        self.draw_tube(painter, tube, motion, values, now, row["connected"])
        painter.setFont(font(7))
        painter.setPen(QColor("#748598"))
        project = Path(row["project"]).name if row["project"] else row["id"][:12]
        extra = row.get("detail", "")
        if not row["connected"]:
            extra = "连接中断 · 上次状态"
        elif row.get("children"):
            extra = f"{row['children']} 个子任务" + (" · " + extra if extra else "")
        painter.drawText(QRectF(38, y + 63, 165, 14), painter.fontMetrics().elidedText(project, Qt.ElideRight, 165))
        painter.drawText(QRectF(202, y + 63, 179, 14), Qt.AlignRight,
                         painter.fontMetrics().elidedText(extra, Qt.ElideRight, 179))
        painter.restore()

    def draw_tube(self, painter, rect, motion, values, now, connected):
        rgb, amp, _, jitter, particles, liquid, brightness = values[:3], *values[3:]
        intensity = self.settings["intensity"]
        clock = now - self.origin_time
        painter.save()
        # A restrained exterior glow; bright effects are clipped to the cavity.
        for width, alpha in ((9, 4), (5, 8), (2, 19)):
            painter.setPen(QPen(color(rgb, alpha * brightness * intensity), width))
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(rect, 11, 11)
        shell = QLinearGradient(rect.topLeft(), rect.bottomLeft())
        shell.setColorAt(0, QColor(68, 83, 102, 180))
        shell.setColorAt(0.13, QColor(16, 25, 37, 250))
        shell.setColorAt(0.65, QColor(6, 11, 19, 255))
        shell.setColorAt(1, QColor(45, 60, 78, 230))
        painter.setBrush(shell)
        painter.setPen(QPen(color(rgb, 75), 0.8))
        painter.drawRoundedRect(rect, 10, 10)
        cavity = rect.adjusted(5, 3, -5, -3)
        clip = QPainterPath()
        clip.addRoundedRect(cavity, 7, 7)
        painter.setClipPath(clip)
        if not connected:
            painter.setOpacity(0.45)
        glow = QRadialGradient(cavity.center(), cavity.width() * 0.55)
        glow.setColorAt(0, color(rgb, 20 * brightness * intensity))
        glow.setColorAt(1, color(rgb, 0))
        painter.fillRect(cavity, glow)
        if liquid > 0.001:
            level = cavity.bottom() - cavity.height() * liquid
            fill = QPainterPath(QPointF(cavity.left(), cavity.bottom()))
            for i in range(65):
                x = i / 64
                surface = level + math.sin(x * 9 + clock * 0.65) * (1 - liquid) * 2
                fill.lineTo(cavity.left() + x * cavity.width(), surface)
            fill.lineTo(cavity.right(), cavity.bottom())
            fill.closeSubpath()
            water = QLinearGradient(cavity.topLeft(), cavity.bottomLeft())
            water.setColorAt(0, color(rgb, 205 * liquid))
            water.setColorAt(0.5, color(rgb, 117 * liquid))
            water.setColorAt(1, color(rgb, 185 * liquid))
            painter.setPen(Qt.NoPen)
            painter.setBrush(water)
            painter.drawPath(fill)
            painter.save()
            painter.setClipPath(fill, Qt.IntersectClip)
            for band in range(3):
                ribbon = QPainterPath()
                for i in range(65):
                    x = i / 64
                    py = cavity.center().y() + math.sin(x * 8 + clock * 0.4 + band * 2) * 5
                    point = QPointF(cavity.left() + x * cavity.width(), py)
                    ribbon.moveTo(point) if i == 0 else ribbon.lineTo(point)
                painter.setPen(QPen(QColor(168, 255, 218, round(15 * liquid)), 3 + band * 2))
                painter.drawPath(ribbon)
            painter.restore()
        electric = 1 - liquid
        # Amplitude already eases between states: the extra strands and free
        # particles fade with it instead of popping on/off at a state boundary.
        activity = min(1, max(0, amp / 0.48))

        def point(x, strand=0):
            phase = motion.phase * (1, -0.78, 1.17, -1.04, 0.67)[strand] + strand * 2.2
            scale = (1, 0.9, 0.76, 1.08, 0.63)[strand]
            return QPointF(cavity.left() + x * cavity.width(), cavity.center().y()
                           + wave(x, phase, clock + strand * 0.7, amp * scale, jitter)
                           * cavity.height() * 0.7 * intensity)

        # Dust-like sparks occupy the depth of the whole cavity, drifting
        # independently of the current. Edge fades hide their wraparound.
        field = activity * particles * electric
        if field > 0.001:
            painter.setPen(Qt.NoPen)
            for i in range(38):
                seed = i * 2.39996323
                direction = 1 if i % 3 else -1
                x = (i * 0.61803398875 + direction * motion.travel * (0.32 + (i % 5) * 0.13)) % 1
                lane = (i * 0.41421356) % 1
                drift = math.sin(motion.phase * 0.8 + seed) * 0.085
                tremor = math.sin(clock * 23 + seed) * jitter * 0.045
                y = 0.14 + lane * 0.72 + (drift + tremor) * intensity
                p = QPointF(cavity.left() + x * cavity.width(), cavity.top() + y * cavity.height())
                edge = min(1, x * 12, (1 - x) * 12)
                shimmer = 0.7 + 0.3 * math.sin(motion.phase + seed) ** 2
                strength = field * edge * shimmer
                radius = 0.5 + (i % 4) * 0.13
                painter.setBrush(color(rgb, 24 * strength))
                painter.drawEllipse(p, radius * 3, radius * 3)
                painter.setBrush(color(rgb, 185 * strength))
                painter.drawEllipse(p, radius, radius)

        if electric > 0.001:
            # Different phases/directions make the strands weave across one
            # another; four colored currents sit behind the primary laser.
            for strand in (4, 3, 2, 1, 0):
                weight = 1 if strand == 0 else activity * 0.72
                if weight < 0.001:
                    continue
                path = QPainterPath()
                for i in range(65):
                    p = point(i / 64, strand)
                    path.moveTo(p) if i == 0 else path.lineTo(p)
                strokes = (((4 + 2 * activity, 34), (1.5 + 0.8 * activity, 165),
                            (0.65 + 0.35 * activity, 225)) if strand == 0 else ((4.5, 30), (1.35, 180)))
                for width, alpha in strokes:
                    painter.setBrush(Qt.NoBrush)
                    tint = (215, 244, 255) if strand == 0 and width <= 1 else rgb
                    painter.setPen(QPen(color(tint, alpha * electric * brightness * weight), width))
                    painter.drawPath(path)
        painter.setPen(Qt.NoPen)
        for i in range(19 if particles * electric > 0.001 else 0):
            x = (i * 0.61803398875 + motion.travel * (0.65 + (i % 4) * 0.13)) % 1
            p = point(x)
            if i % 5 and activity > 0:
                other = point(x, i % 5)
                p += (other - p) * activity
            edge = min(1, x * 16, (1 - x) * 16)
            strength = edge * (0.35 + 0.65 * math.sin(math.pi * x)) * particles * electric
            painter.setBrush(color(rgb, 32 * strength))
            painter.drawEllipse(p, 3.4, 3.4)
            painter.setBrush(QColor(232, 252, 255, round(220 * strength)))
            painter.drawEllipse(p, 0.8 + (i % 3) * 0.16, 0.8 + (i % 3) * 0.16)
        painter.setClipping(False)
        painter.setOpacity(1)
        painter.setPen(QPen(QColor(211, 231, 243, 38), 0.8))
        painter.drawLine(QPointF(rect.left() + 14, rect.top() + 3), QPointF(rect.right() - 14, rect.top() + 3))
        for x in (rect.left() - 1, rect.right() - 5):
            painter.setBrush(QColor("#354253"))
            painter.setPen(QPen(QColor("#576779"), 0.6))
            painter.drawRoundedRect(QRectF(x, rect.top() + 7, 6, 12), 2, 2)
        painter.restore()

    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton:
            return
        if QRectF(366, 17, 32, 32).contains(event.pos()):
            self.hide()
        elif QRectF(333, 17, 32, 32).contains(event.pos()):
            self.menu.popup(event.globalPos())
        elif event.pos().y() < self.HEADER:
            self.drag = event.globalPos() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if self.drag is not None:
            self.move(event.globalPos() - self.drag)
            return
        index = int((event.pos().y() - self.HEADER) // self.ROW)
        if 0 <= index < len(self.rows):
            row = self.rows[index]
            self.setToolTip(f"{row['title']}\n{row['project']}\n{row['id']}\n{row.get('detail', '')}")
        else:
            self.setToolTip("拖动标题栏移动面板")

    def mouseReleaseEvent(self, _):
        if self.drag is not None:
            self.drag = None
            self.settings["position"] = [self.x(), self.y()]
            self.save_settings()
