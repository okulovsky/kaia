import io
from pathlib import Path
from typing import Callable
from PyQt6.QtWidgets import (
    QWidget, QLabel, QHBoxLayout, QVBoxLayout, QScrollArea,
    QGridLayout, QComboBox, QCheckBox, QMenu, QSizePolicy, QLayout
)
from PyQt6.QtGui import QPixmap, QImage, QKeyEvent
from PyQt6.QtCore import Qt, QRect, QPoint, QSize
from PIL import Image
from yo_fluq import FileIO
from .tag_annotation import TagAnnotation, GlobalTags
from .tag_button import TagButton


class FlowLayout(QLayout):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._items = []

    def addItem(self, item):
        self._items.append(item)

    def count(self):
        return len(self._items)

    def itemAt(self, index):
        return self._items[index] if 0 <= index < len(self._items) else None

    def takeAt(self, index):
        return self._items.pop(index) if 0 <= index < len(self._items) else None

    def expandingDirections(self):
        return Qt.Orientation(0)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self._layout(QRect(0, 0, width, 0), dry_run=True)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._layout(rect, dry_run=False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for item in self._items:
            size = size.expandedTo(item.minimumSize())
        m = self.contentsMargins()
        return size + QSize(m.left() + m.right(), m.top() + m.bottom())

    def _layout(self, rect, dry_run):
        x, y, line_h = rect.x(), rect.y(), 0
        sp = self.spacing()
        for item in self._items:
            w = item.sizeHint().width()
            h = item.sizeHint().height()
            if x + w > rect.right() and line_h > 0:
                x = rect.x()
                y += line_h + sp
                line_h = 0
            if not dry_run:
                item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))
            x += w + sp
            line_h = max(line_h, h)
        return y + line_h - rect.y()


def _image_to_pixmap(path: Path, max_width=640, max_height=480) -> QPixmap:
    image = Image.open(str(path))
    scale = min(max_width / image.width, max_height / image.height, 1.0)
    image = image.resize((int(image.width * scale), int(image.height * scale)))
    buf = io.BytesIO()
    image.save(buf, format='PNG')
    qi = QImage()
    qi.loadFromData(buf.getvalue())
    return QPixmap(qi)


class _GlobalTagLabel(QLabel):
    """Single tag item in the global tags display; right-click to remove."""
    def __init__(self, tag: str, on_remove: callable):
        super().__init__(tag)
        self.tag = tag
        self.on_remove = on_remove

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        remove_action = menu.addAction('Remove')
        action = menu.exec(event.globalPos())
        if action == remove_action:
            self.on_remove(self.tag)


class MainWindow(QWidget):
    GRID_COLS = 3

    def __init__(self, cases, all_tags: list[str], case_to_file: Callable, cache):
        super().__init__()
        self.cases = cases
        self.all_tags = all_tags
        self.case_to_file = case_to_file
        self.cache = cache
        self.case_index = cache.find_start_index([c.get_id() for c in cases])

        self._global_tags_path = cache.folder / 'global.json'

        self.setWindowTitle('Tagger')

        # ── filename label + reject checkbox ──
        self.filename_label = QLabel()
        self.index_label = QLabel()
        self.reject_checkbox = QCheckBox('Reject image')
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.addWidget(self.index_label)
        header_layout.addWidget(self.filename_label)
        header_layout.addWidget(self.reject_checkbox)
        header_layout.addStretch()

        # ── image ──
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        # ── search bar ──
        self.search_bar = QComboBox()
        self.search_bar.setEditable(True)
        self.search_bar.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.search_bar.lineEdit().setPlaceholderText('Search tags…')
        self.search_bar.addItems(all_tags)
        self.search_bar.setCurrentIndex(-1)
        completer = self.search_bar.completer()
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setFilterMode(Qt.MatchFlag.MatchStartsWith)
        self.search_bar.textActivated.connect(self._on_tag_selected)

        # ── tag grid (inside scroll area) ──
        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        scroll = QScrollArea()
        scroll.setWidget(self.grid_widget)
        scroll.setWidgetResizable(True)
        scroll.setMinimumWidth(280)

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.addWidget(self.search_bar)
        right_layout.addWidget(scroll)

        # ── middle row: image + right panel ──
        middle = QWidget()
        middle_layout = QHBoxLayout(middle)
        middle_layout.setContentsMargins(0, 0, 0, 0)
        middle_layout.addWidget(self.image_label)
        middle_layout.addWidget(right_panel)

        # ── global tags display ──
        self.global_accepted_widget = QWidget()
        self.global_accepted_layout = FlowLayout(self.global_accepted_widget)
        self.global_accepted_layout.setContentsMargins(0, 0, 0, 0)

        self.global_rejected_widget = QWidget()
        self.global_rejected_layout = FlowLayout(self.global_rejected_widget)
        self.global_rejected_layout.setContentsMargins(0, 0, 0, 0)

        # ── root layout ──
        root = QVBoxLayout(self)
        root.addWidget(header)
        root.addWidget(middle)
        root.addWidget(QLabel('<b>Global accepted:</b>'))
        root.addWidget(self.global_accepted_widget)
        root.addWidget(QLabel('<b>Global rejected:</b>'))
        root.addWidget(self.global_rejected_widget)

        self._load()

    # ── persistence helpers ──

    def _read_global_tags(self) -> GlobalTags:
        if self._global_tags_path.is_file():
            return GlobalTags(**FileIO.read_json(self._global_tags_path))
        return GlobalTags()

    def _write_global_tags(self, gt: GlobalTags):
        FileIO.write_json(gt.__dict__, self._global_tags_path)

    # ── loading a case ──

    def _load(self):
        case = self.cases[self.case_index]
        self.filename_label.setText(case.get_id())
        self.index_label.setText(f'{self.case_index + 1}/{len(self.cases)}')
        pixmap = _image_to_pixmap(self.case_to_file(case))
        self.image_label.setPixmap(pixmap)
        self.image_label.setFixedSize(pixmap.size())
        existing = self.cache.get_annotation(case.get_id())
        self.reject_checkbox.setChecked(existing.get('rejected', False) if existing else False)
        self._rebuild_grid()
        self._rebuild_global_display()

    def _current_button_states(self) -> dict[str, bool]:
        states = {}
        for i in range(self.grid_layout.count()):
            btn = self.grid_layout.itemAt(i).widget()
            if isinstance(btn, TagButton):
                states[btn.tag] = btn.state
        return states

    def _resolve_tags(self, overrides: dict[str, bool]) -> dict[str, bool]:
        case = self.cases[self.case_index]
        existing = self.cache.get_annotation(case.get_id())
        gt = self._read_global_tags()

        auto_tags = set(case.auto_tags or {})
        stored_tags = set(existing['tags'].keys()) if existing else set()
        extra_tags = set(overrides.keys())
        tag_names = auto_tags | stored_tags | extra_tags

        tags = {}
        for tag in tag_names:
            if tag in overrides:
                tags[tag] = overrides[tag]
            elif existing and tag in existing['tags']:
                tags[tag] = existing['tags'][tag]
            elif tag in gt.accepted:
                tags[tag] = True
            elif tag in gt.rejected:
                tags[tag] = False
            else:
                tags[tag] = True  # auto_tags default
        return tags

    def _rebuild_grid(self, preserve_current: bool = False):
        overrides = self._current_button_states() if preserve_current else {}
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        tags = self._resolve_tags(overrides)
        for i, (tag, state) in enumerate(sorted(tags.items())):
            btn = TagButton(tag, state, self._on_global_change)
            self.grid_layout.addWidget(btn, i // self.GRID_COLS, i % self.GRID_COLS)

    def _rebuild_global_display(self):
        gt = self._read_global_tags()

        for layout in (self.global_accepted_layout, self.global_rejected_layout):
            while layout.count():
                item = layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

        for tag in gt.accepted:
            lbl = _GlobalTagLabel(tag, lambda t: self._on_global_remove(t, accepted=True))
            lbl.setStyleSheet('color: #2e7d32; margin: 2px 4px;')
            self.global_accepted_layout.addWidget(lbl)

        for tag in gt.rejected:
            lbl = _GlobalTagLabel(tag, lambda t: self._on_global_remove(t, accepted=False))
            lbl.setStyleSheet('color: #c62828; margin: 2px 4px;')
            self.global_rejected_layout.addWidget(lbl)

    # ── callbacks ──

    def _on_tag_selected(self, tag: str):
        self.search_bar.setCurrentIndex(-1)
        self.search_bar.clearEditText()
        # check if already present
        for i in range(self.grid_layout.count()):
            btn = self.grid_layout.itemAt(i).widget()
            if isinstance(btn, TagButton) and btn.tag == tag:
                return
        count = self.grid_layout.count()
        btn = TagButton(tag, True, self._on_global_change)
        self.grid_layout.addWidget(btn, count // self.GRID_COLS, count % self.GRID_COLS)

    def _on_global_change(self, tag: str, accepted: bool):
        gt = self._read_global_tags()
        # remove from both lists first
        gt.accepted = [t for t in gt.accepted if t != tag]
        gt.rejected = [t for t in gt.rejected if t != tag]
        if accepted:
            gt.accepted.append(tag)
        else:
            gt.rejected.append(tag)
        self._write_global_tags(gt)
        self._rebuild_grid(preserve_current=True)
        self._rebuild_global_display()

    def _on_global_remove(self, tag: str, accepted: bool):
        gt = self._read_global_tags()
        if accepted:
            gt.accepted = [t for t in gt.accepted if t != tag]
        else:
            gt.rejected = [t for t in gt.rejected if t != tag]
        self._write_global_tags(gt)
        self._rebuild_global_display()

    # ── save + advance ──

    def _save_current(self):
        case = self.cases[self.case_index]
        tags = {}
        for i in range(self.grid_layout.count()):
            btn = self.grid_layout.itemAt(i).widget()
            if isinstance(btn, TagButton):
                tags[btn.tag] = btn.state
        self.cache.add(case.get_id(), {'tags': tags, 'rejected': self.reject_checkbox.isChecked()})

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Space:
            self._save_current()
            statuses = self.cache.get_annotation_status()
            if all(s.annotated for s in statuses.values()):
                self.close()
                return
            self.case_index = (self.case_index + 1) % len(self.cases)
            self._load()
        else:
            super().keyPressEvent(event)
