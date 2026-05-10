import os
from pathlib import Path
from typing import Any
from yo_fluq import FileIO
from ..core import IAnnotationCache, AnnotationStatus


class PyQtAnnotationCache(IAnnotationCache):
    def __init__(self, folder: Path, ids: list[str]):
        self.folder = folder
        self.ids = ids

    @property
    def _ann_folder(self) -> Path:
        return self.folder / 'annotations'

    def _path(self, id: str) -> Path:
        return self._ann_folder / f'{id}.json'

    def add(self, id: str, value: dict):
        os.makedirs(self._ann_folder, exist_ok=True)
        FileIO.write_json(value, self._path(id))

    def remove(self, id: str):
        p = self._path(id)
        if p.is_file():
            p.unlink()

    def get_annotation(self, id: str) -> Any | None:
        p = self._path(id)
        if p.is_file():
            return FileIO.read_json(p)
        return None

    def undo(self):
        ann_folder = self._ann_folder
        if not ann_folder.exists():
            return
        files = list(ann_folder.glob('*.json'))
        if not files:
            return
        max(files, key=lambda f: f.stat().st_mtime).unlink()

    def get_annotation_status(self) -> dict[str, AnnotationStatus]:
        ann_folder = self._ann_folder
        return {
            id: AnnotationStatus(value=True) if (ann_folder / f'{id}.json').is_file() else AnnotationStatus()
            for id in self.ids
        }

    def get_summary(self) -> str:
        statuses = self.get_annotation_status()
        annotated = sum(1 for s in statuses.values() if s.annotated)
        return f'{annotated} annotated, {len(self.ids) - annotated} remaining'

    def finish_annotation(self):
        (self.folder / '.finished').write_text('')

    def get_result(self) -> dict[str, Any]:
        ann_folder = self._ann_folder
        if not ann_folder.exists():
            return {}
        return {p.stem: FileIO.read_json(p) for p in ann_folder.glob('*.json')}
