from pathlib import Path
from typing import Callable, Generic
from chara import TCase
from chara.common.pipelines.annotation.pyqt_annotator import PyQtAnnotationCache, PyQtAnnotator
from .crop_rect import CropRect
from .croper import MainWindow


class CropAnnotator(Generic[TCase], PyQtAnnotator[TCase]):
    def __init__(self, case_to_file: Callable):
        self.case_to_file = case_to_file

    def create_main_window(self, cases, cache):
        return MainWindow(cases, self.case_to_file, cache)

    def get_result(self, folder: Path) -> dict[str, CropRect]:
        cache = PyQtAnnotationCache(folder, [])
        result = {}
        for id, data in cache.get_result().items():
            if data is not None:
                result[id] = CropRect(**data)
        return result
