from pathlib import Path
from typing import Generic, Callable
from chara import TCase
from chara.common.pipelines.annotation.pyqt_annotator import PyQtAnnotator, PyQtAnnotationCache
from .tag_annotation import TagAnnotation
from .main_window import MainWindow


class TagAnnotator(Generic[TCase], PyQtAnnotator[TCase]):
    def __init__(self, all_tags: list[str], case_to_file: Callable):
        self.all_tags = all_tags
        self.case_to_file = case_to_file

    def create_main_window(self, cases, cache):
        return MainWindow(cases, self.all_tags, self.case_to_file, cache)

    def get_result(self, folder: Path) -> dict[str, TagAnnotation]:
        cache = PyQtAnnotationCache(folder, [])
        return {
            id: TagAnnotation(**data)
            for id, data in cache.get_result().items()
            if data is not None
        }
