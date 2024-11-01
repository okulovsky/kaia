from typing import Optional
from dataclasses import dataclass
import os
from .image_tools import ConvertImage
import subprocess
from pathlib import Path
import sys
from .crop_rect import CropRect
from kaia.infra import FileIO
import copy

class Folders:
    source = 'source'
    crop_schemas = 'crop_schemas'
    crop = 'cropped'
    upscale = 'upscale'
    interrogation = 'interrogation'
    annotation = 'annotation'
    annotation_settings_filename = 'annotation_settings.json'

@dataclass
class AnnotationSettings:

    path: Path
    tags: list[str]
    exclude_tags: list[str]
    include_tags: list[str]

    @staticmethod
    def load(folder: Path) -> 'AnnotationSettings':
        path = folder/Folders.annotation_settings_filename
        if not path.is_file():
            return AnnotationSettings(path, [], [], [])
        else:
            return AnnotationSettings(path, **FileIO.read_json(path))

    def save(self):
        d = copy.deepcopy(self.__dict__)
        del d['path']
        FileIO.write_json(d, self.path)




@dataclass
class Status:
    source_path: Path
    crop_schema_path: Path|None = None
    crop_rect: CropRect | None = None
    cropped_path: Path | None = None
    upscaled_path: Path | None = None
    interrogation_path: Path | None = None
    interrogation_tags: dict[str,float]|None = None
    annotation_path: Path | None = None
    annotated_tags: tuple[str] = None


    def build_crop_schema_path(self):
        base_folder = self.source_path
        return base_folder.parent.parent / Folders.crop_schemas / (base_folder.name + '.json')


    def _build_path_for_uid(self, folder, extension):
        return self.crop_schema_path.parent.parent/folder/(self.crop_rect.uuid+extension)

    def build_cropped_path(self):
        return self._build_path_for_uid(Folders.crop, '.png')

    def build_upscaled_path(self):
        return self._build_path_for_uid(Folders.upscale, '.png')

    def build_interrogation_path(self):
        return self._build_path_for_uid(Folders.interrogation, '.json')


    def build_annotation_path(self):
        return self._build_path_for_uid(Folders.annotation, '.pkl')


    def get_annotation_settings(self):
        return AnnotationSettings.load(self.source_path.parent.parent)

    def update(self):
        if not self.build_crop_schema_path().is_file():
            return self
        self.crop_schema_path = self.build_crop_schema_path()
        self.crop_rect = CropRect(**FileIO.read_json(self.crop_schema_path))

        if self.build_cropped_path().is_file():
            self.cropped_path = self.build_cropped_path()

        if self.build_upscaled_path().is_file():
            self.upscaled_path = self.build_upscaled_path()

        if self.build_interrogation_path().is_file():
            self.interrogation_path = self.build_interrogation_path()
            self.interrogation_tags = FileIO.read_json(self.interrogation_path)

        if self.build_annotation_path().is_file():
            self.annotation_path = self.build_annotation_path()
        return self

    @staticmethod
    def gather(root_folder: Path, name: str) -> Optional['Status']:
        status = Status(root_folder/Folders.source/name)
        if not status.source_path.is_file():
            return None
        return status.update()



    @staticmethod
    def gather_all(root_folder: Path):
        statuses = []
        for file in os.listdir(root_folder / Folders.source):
            statuses.append(Status.gather(root_folder, file))
        return statuses


