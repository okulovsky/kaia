import os
from typing import *
from abc import ABC, abstractmethod
from dataclasses import dataclass
from ...upsampling import UpsamplingItem
from pathlib import Path
import zipfile
from yo_fluq import *

@dataclass
class ExportItem:
    filename: str
    character: str
    text: str
    duration: float
    content_description: Any = None


class IExporter(ABC):
    @abstractmethod
    def export(self, item: UpsamplingItem) -> ExportItem:
        pass

    @abstractmethod
    def get_content(self, item: ExportItem) -> bytes:
        pass

    def export_to_zip(self, objects: list[ExportItem], path: Path):
        with zipfile.ZipFile(path, 'w') as file:
            for item in objects:
                file.writestr(item.character+'/'+item.filename, self.get_content(item))
                file.writestr(item.character+'/'+item.filename.replace('.wav', '.txt'), item.text.encode('utf-8'))

    def export_to_folder(self, objects: list[ExportItem], path: Path, with_texts: bool = True):
        path = Path(path)
        if path.is_dir() or path.is_file():
            raise ValueError(f"Path {path} exists, cannot export")
        for item in objects:
            p = path/item.character
            os.makedirs(p, exist_ok=True)
            FileIO.write_bytes(self.get_content(item), p/item.filename)
            if with_texts:
                FileIO.write_bytes(item.text.encode('utf-8'), p/(item.filename.replace('.wav','.txt')))


