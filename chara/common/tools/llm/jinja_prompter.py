from pathlib import Path
from typing import Iterable, Any
from jinja2 import FileSystemLoader, Environment
from copy import copy


class JinjaPrompter:
    def __init__(self,
                 file: Path,
                 additional_folders: Iterable[Path] = (),
                 additional_objects: dict[str, Any]|None = None,
                 main_field: str = 'case'
                 ):
        folders = [file.parent] + list(additional_folders)
        loader = FileSystemLoader(folders)
        self.env = Environment(loader=loader, autoescape=False)
        self.template = self.env.get_template(file.name)
        self.additional_objects = additional_objects if additional_objects is not None else {}
        self.main_field = main_field

    def __call__(self, obj: Any) -> Any:
        data = copy(self.additional_objects)
        data[self.main_field] = obj
        return self.template.render(data)



