from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QHBoxLayout, QVBoxLayout
from PyQt6.QtGui import QPainter, QPen, QKeyEvent, QImage, QWheelEvent, QMouseEvent, QPixmap
from PyQt6.QtCore import Qt
from copy import deepcopy
from PIL import Image
from pathlib import Path
from typing import Callable
import io
from .crop_rect import CropRect


def image_to_qimage(image):
    buf = io.BytesIO()
    image.save(buf, format='PNG')
    qi = QImage()
    qi.loadFromData(buf.getvalue())
    return qi


class ImageHolder(QLabel):
    def __init__(self, parent, on_change):
        super().__init__(parent)
        self.on_change = on_change
        self.setMouseTracking(True)
        self.max_width = 640
        self.max_height = 480
        self.size_delta = 16

    def load(self, path, rects):
        self.path = path
        image = Image.open(str(path))
        width = min(self.max_width, image.width)
        height = min(self.max_height, image.height)
        self.scale = min(width / image.width, height / image.height)
        image = image.resize((int(self.scale * image.width), int(self.scale * image.height)))
        self.image = image_to_qimage(image)
        self.setFixedSize(self.image.width(), self.image.height())
        self.current_rect = CropRect(0, 0, size=512 * self.scale)
        self.size_delta = 16 * self.scale
        self.selected_rects = [r.scale(self.scale) for r in rects] if rects is not None else []

    def wheelEvent(self, a0: QWheelEvent):
        modifiers = QApplication.keyboardModifiers()
        if modifiers == Qt.KeyboardModifier.ControlModifier:
            self.current_rect.angle += 10 if a0.angleDelta().y() > 0 else -10
        else:
            delta = 1 if modifiers == Qt.KeyboardModifier.ShiftModifier else self.size_delta
            self.current_rect.size += delta if a0.angleDelta().y() > 0 else -delta
        self.update()

    def mouseMoveEvent(self, event: QMouseEvent):
        self.current_rect.center_x = int(event.position().x())
        self.current_rect.center_y = int(event.position().y())
        self.current_rect = self.current_rect.try_put_in_bound(self.image.width(), self.image.height())
        self.update()

    def mousePressEvent(self, ev: QMouseEvent):
        if ev.buttons() == Qt.MouseButton.LeftButton:
            if self.current_rect.is_bounded(self.image.width(), self.image.height()):
                self.selected_rects = [deepcopy(self.current_rect)]
        else:
            self.selected_rects = []
        self.update()
        self.on_change()

    def draw_rect(self, qp: QPainter, rect: CropRect, color):
        qp.setPen(QPen(color, 3))
        points = rect.get_locs()
        for i in range(4):
            qp.drawLine(
                int(points[i][0]), int(points[i][1]),
                int(points[(i + 1) % 4][0]), int(points[(i + 1) % 4][1])
            )

    def paintEvent(self, a0):
        qp = QPainter()
        qp.begin(self)
        qp.drawImage(0, 0, self.image)
        bounded = self.current_rect.is_bounded(self.image.width(), self.image.height())
        self.draw_rect(qp, self.current_rect, Qt.GlobalColor.green if bounded else Qt.GlobalColor.red)
        for r in self.selected_rects:
            self.draw_rect(qp, r, Qt.GlobalColor.gray if r.is_bounded(self.image.width(), self.image.height()) else Qt.GlobalColor.darkRed)
        qp.end()


class MainWindow(QWidget):
    def __init__(self, cases, case_to_file: Callable, cache):
        self.cases = cases
        self.case_index = cache.find_start_index([c.get_id() for c in cases])
        self.case_to_file = case_to_file
        self.cache = cache

        super().__init__()
        self.setWindowTitle("Croper")

        self.image = ImageHolder(self, self.on_change)
        self.panel = QWidget(self)
        self.panel_layout = QHBoxLayout(self.panel)
        self.filename_label = QLabel()
        self.size_label = QLabel()

        layout = QVBoxLayout(self)
        layout.addWidget(self.filename_label)
        layout.addWidget(self.image)
        layout.addWidget(self.size_label)
        layout.addWidget(self.panel)

        self.load()

    def load(self):
        case = self.cases[self.case_index]
        path = self.case_to_file(case)
        existing = self.cache.get_annotation(case.get_id())
        rects = [CropRect(**existing)] if existing is not None else None
        self.image.load(path, rects)
        self.filename_label.setText(path.name)
        self.on_change()
        self.resize(self.image.width(), self.image.height() + 200)

    def on_change(self):
        case = self.cases[self.case_index]
        rects = [r.scale(1 / self.image.scale) for r in self.image.selected_rects]
        self.size_label.setText(', '.join(str(r.size) for r in rects))

        if len(rects) == 0:
            self.cache.add(case.get_id(), None)
        else:
            self.cache.add(case.get_id(), rects[0].__dict__)

        im = Image.open(self.image.path)
        for i in reversed(range(self.panel_layout.count())):
            self.panel_layout.itemAt(i).widget().setParent(None)
        for r in rects:
            cropped = r.crop(im).resize((100, 100))
            label = QLabel()
            label.setPixmap(QPixmap(image_to_qimage(cropped)))
            label.resize(100, 100)
            self.panel_layout.addWidget(label)

    def keyPressEvent(self, a0: QKeyEvent):
        if a0.key() == Qt.Key.Key_Space:
            delta = -1 if a0.modifiers() == Qt.KeyboardModifier.ShiftModifier else +1
            self.case_index = (self.case_index + delta) % len(self.cases)
            self.load()
