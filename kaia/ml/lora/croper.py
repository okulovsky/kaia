import os
import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QHBoxLayout, QVBoxLayout
from PyQt5.QtGui import QPainter, QPen, QKeyEvent
from PyQt5.QtGui import QImage, QWheelEvent, QMouseEvent, QPixmap
from PyQt5.QtCore import Qt
from copy import deepcopy
from kaia.infra import FileIO
from yo_fluq_ds import Query
from PIL import Image
import io
from .crop_rect import CropRect
from .status import Status, Folders
from pathlib import Path
import sys

def image_to_qimage(image):
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='PNG')
    qi = QImage()
    qi.loadFromData(img_byte_arr.getvalue())
    return qi


class ImageHolder(QLabel):
    def __init__(self, parent, on_change):
        super(ImageHolder, self).__init__(parent)
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
        self.scale = min(width/image.width, height/image.height)
        image = image.resize((int(self.scale*image.width), int(self.scale*image.height)))
        self.image = image_to_qimage(image)
        self.setFixedSize(self.image.width(), self.image.height())
        self.current_rect = CropRect(0, 0, size = 512*self.scale)
        self.size_delta = 16*self.scale
        if rects is not None:
            self.selected_rects=[r.scale(self.scale) for r in rects]
        else:
            self.selected_rects = []


    def wheelEvent(self, a0: QWheelEvent):
        modifiers = QApplication.keyboardModifiers()
        if modifiers == Qt.ControlModifier:
            if a0.angleDelta().y() > 0:
                self.current_rect.angle += 10
            else:
                self.current_rect.angle -= 10
        else:
            delta = self.size_delta
            if modifiers == Qt.ShiftModifier:
                delta=1
            if a0.angleDelta().y()>0:
                self.current_rect.size+=delta
            else:
                self.current_rect.size-=delta
        self.update()


    def mouseMoveEvent(self, event):
        self.current_rect.center_x = event.pos().x()
        self.current_rect.center_y = event.pos().y()
        self.current_rect = self.current_rect.try_put_in_bound(self.image.width(), self.image.height())
        self.update()

    def mousePressEvent(self, ev: QMouseEvent) -> None:
        if ev.buttons()==Qt.LeftButton:
            if self.current_rect.is_bounded(self.image.width(), self.image.height()):
                self.selected_rects = [deepcopy(self.current_rect)]
        else:
            rects = []
            self.selected_rects = rects
        self.update()
        self.on_change()

    def draw_rect(self,qp: QPainter, rect: CropRect, color):
        qp.setPen(QPen(color,3))
        points = rect.get_locs()
        for i in range(4):
            qp.drawLine(
                int(points[i][0]),
                int(points[i][1]),
                int(points[(i+1)%4][0]),
                int(points[(i+1)%4][1])
            )


    def paintEvent(self, a0) -> None:
        qp = QPainter()
        qp.begin(self)
        qp.drawImage(0, 0, self.image)
        bounded = self.current_rect.is_bounded(self.image.width(), self.image.height())
        self.draw_rect(qp, self.current_rect, Qt.green if bounded else Qt.red)
        for r in self.selected_rects:
            bounded = r.is_bounded(self.image.width(), self.image.height())
            self.draw_rect(qp, r, Qt.gray if bounded else Qt.darkRed)
        qp.end()


class MainWindow(QWidget):
    def __init__(self,
                 root_folder: Path,
                 ):
        statuses = Status.gather_all(root_folder)
        self.files = [status.source_path for status in sorted(statuses, key = lambda z: z.cropped_path is not None)]

        self.file_index = 0
        super(MainWindow, self).__init__()

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
        current_file = self.files[self.file_index]
        schema_path = Status(current_file).build_crop_schema_path()
        if schema_path.is_file():
            js = FileIO.read_json(schema_path)
            rect = CropRect(**js)
            rects = [rect]
        else:
            rects = None
        self.image.load(current_file, rects)
        self.filename_label.setText(current_file.name)
        self.on_change()
        self.resize(self.image.width(), self.image.height()+200)

    def on_change(self):
        rects = [r.scale(1/self.image.scale) for r in self.image.selected_rects]
        sizes = ', '.join(str(r.size) for r in rects)
        self.size_label.setText(sizes)

        schema_path = Status(self.image.path).build_crop_schema_path()
        os.makedirs(schema_path.parent, exist_ok=True)
        if len(rects) == 0:
            if schema_path.is_file():
                os.unlink(schema_path)
        else:
            FileIO.write_json(rects[0].__dict__, schema_path)

        im = Image.open(self.image.path)
        for i in reversed(range(self.panel_layout.count())):
            self.panel_layout.itemAt(i).widget().setParent(None)
        for r in rects:
            i = r.crop(im).resize((100,100))
            qi = image_to_qimage(i)
            label = QLabel()
            bt = QPixmap(qi)
            label.setPixmap(bt)
            label.resize(qi.width(), qi.height())
            self.panel_layout.addWidget(label)

    def keyPressEvent(self, a0: QKeyEvent) -> None:
        if a0.key() == Qt.Key_Space:
            delta = +1
            if a0.modifiers() == Qt.ShiftModifier:
                delta = -1
            self.file_index = (self.file_index+delta)%len(self.files)
            self.load()


def run_croper(folder: Path):
    app = QApplication(sys.argv)
    widget = MainWindow(folder)
    widget.setWindowTitle("Croper")
    widget.show()
    app.exec_()

