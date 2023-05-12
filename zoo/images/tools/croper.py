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

    def load(self, path):
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
        try:
            rects = FileIO.read_jsonpickle(str(path)+'.crop.json')
            self.selected_rects=[r.scale(self.scale) for r in rects]
        except:
            self.selected_rects = []


    def wheelEvent(self, a0: QWheelEvent):
        modifiers = QApplication.keyboardModifiers()
        if modifiers == Qt.ControlModifier:
            if a0.angleDelta().y() > 0:
                self.current_rect.angle += 10
            else:
                self.current_rect.angle -= 10
        else:
            if a0.angleDelta().y()>0:
                self.current_rect.size+=self.size_delta
            else:
                self.current_rect.size-=self.size_delta
        self.update()


    def mouseMoveEvent(self, event):
        self.current_rect.center_x = event.pos().x()
        self.current_rect.center_y = event.pos().y()
        self.current_rect = self.current_rect.try_put_in_bound(self.image.width(), self.image.height())
        self.update()

    def mousePressEvent(self, ev: QMouseEvent) -> None:
        if ev.buttons()==Qt.LeftButton:
            self.selected_rects.append(deepcopy(self.current_rect))
        else:
            rects = [r for r in self.selected_rects if not r.contains(ev.pos().x(), ev.pos().y())]
            self.selected_rects = rects
        self.update()
        self.on_change()

    def draw_rect(self,qp: QPainter, rect: CropRect, color):
        qp.setPen(QPen(color,3))
        points = rect.get_locs()
        for i in range(4):
            qp.drawLine(points[i][0], points[i][1], points[(i+1)%4][0], points[(i+1)%4][1])


    def paintEvent(self, a0) -> None:
        qp = QPainter()
        qp.begin(self)
        qp.drawImage(0, 0, self.image)
        self.draw_rect(qp, self.current_rect, Qt.red)
        for r in self.selected_rects:
            self.draw_rect(qp, r, Qt.gray)
        qp.end()


class MainWindow(QWidget):
    def __init__(self, folder):
        ext = {'png','jpg','jpeg','jfif'}
        self.files = Query.folder(folder).where(lambda z: z.name.split('.')[-1].lower() in ext).order_by(lambda z: z.name).to_list()

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
        self.image.load(self.files[self.file_index])
        self.filename_label.setText(self.files[self.file_index].name)
        self.on_change()
        #self.panel.resize(self.image.width(), 200)
        self.resize(self.image.width(), self.image.height()+200)

    def on_change(self):
        rects = [r.scale(1/self.image.scale) for r in self.image.selected_rects]
        sizes = ', '.join(str(r.size) for r in rects)
        self.size_label.setText(sizes)
        FileIO.write_jsonpickle(rects, str(self.image.path)+'.crop.json')
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


def run_croper(folder):
    app = QApplication(sys.argv)
    widget = MainWindow(folder)
    widget.setWindowTitle("Croper")
    widget.show()
    app.exec_()
