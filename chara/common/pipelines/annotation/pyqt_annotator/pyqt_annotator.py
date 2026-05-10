import sys
from abc import abstractmethod
from pathlib import Path
from typing import Generic, Any
from PyQt5.QtWidgets import QApplication, QWidget
from ..core import IAnnotator, TCase
from .pyqt_annotation_cache import PyQtAnnotationCache


class PyQtAnnotator(Generic[TCase], IAnnotator[TCase]):
    @abstractmethod
    def create_main_window(self, cases: list[TCase], cache: PyQtAnnotationCache) -> QWidget:
        ...

    def run(self, cases: list[TCase], folder: Path):
        ids = [c.get_id() for c in cases]
        cache = PyQtAnnotationCache(folder, ids)
        app = QApplication(sys.argv)
        window = self.create_main_window(cases, cache)
        window.show()
        app.exec_()
        statuses = cache.get_annotation_status()
        not_annotated = [id for id, s in statuses.items() if not s.annotated]
        if not_annotated:
            raise RuntimeError(
                f"Annotation incomplete: {len(not_annotated)} of {len(ids)} cases not annotated"
            )
        cache.finish_annotation()
