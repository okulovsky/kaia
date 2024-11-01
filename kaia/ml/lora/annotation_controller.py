from pathlib import Path
from .status import  Status, AnnotationSettings
from dataclasses import dataclass, field
from kaia.infra import FileIO
import os

@dataclass
class Annotation:
    @dataclass
    class Tag:
        name: str
        status: bool
        weight: float

    @dataclass
    class Stored:
        tags: list['Annotation.Tag'] | None = None
        new_tags: list[str] | None = None
        skipped: bool = False
        reviewed: bool = False

    status: Status
    settings: AnnotationSettings
    stored: 'Annotation.Stored' = field(default_factory=lambda: Annotation.Stored())

    def change_status(self, tag_name: str):
        for tag in self.stored.tags:
            if tag.name == tag_name:
                tag.status = not tag.status
                return tag.status
        raise ValueError(f"Unknown tag {tag_name}")

    def get_tags_list(self):
        return [t for t in self.stored.tags if t.name not in self.settings.exclude_tags]

    def load(self):
        self.stored = Annotation.Stored(**FileIO.read_pickle(self.status.annotation_path))



class AnnotationController:
    def __init__(self,
                 root_folder: Path,
                 ):
        self.root_folder = root_folder
        self.annotation_settings = AnnotationSettings.load(root_folder)
        self.annotations = []
        for status in Status.gather_all(root_folder):
            if status.cropped_path is None or status.interrogation_path is None:
                continue
            annotation = Annotation(status, self.annotation_settings)
            self.annotations.append(annotation)
            if status.annotation_path is not None:
                annotation.load()
                continue
            annotation.stored.new_tags = []
            annotation.stored.tags = []
            for tag, value in sorted(annotation.status.interrogation_tags.items(), key = lambda z: z[1], reverse=True):
                annotation.stored.tags.append(Annotation.Tag(tag, tag not in self.annotation_settings.exclude_tags, value))

        self.current_index = 0

    @property
    def current(self) -> Annotation:
        return self.annotations[self.current_index]

    def change_index(self, delta: int):
        self.current_index = (self.current_index + delta) % len(self.annotations)

    def save(self):
        self.current.stored.reviewed = True
        os.makedirs(self.current.status.build_annotation_path().parent, exist_ok=True)
        FileIO.write_pickle(self.current.stored.__dict__, self.current.status.build_annotation_path())
        self.annotation_settings.save()


        
















