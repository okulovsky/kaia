from dataclasses import dataclass
from chara import IAnnotationCase
from .cropping import CropRect
from .tagging import TagAnnotation
from pathlib import Path

@dataclass
class DatasetImageCase(IAnnotationCase):
    source: Path
    crop: CropRect|None = None
    upscaled_local_path: Path|None = None
    auto_tags: dict|None = None
    tag_annotation: TagAnnotation|None = None

    def get_id(self) -> str:
        return self.source.name