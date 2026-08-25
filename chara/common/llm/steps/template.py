from typing import Any, Iterable

from .step import LLMRequestStep
from pathlib import Path
from jinja2 import FileSystemLoader, Environment


class JinjaTemplate(LLMRequestStep):
    def __init__(self,
                 file: Path | str,
                 additional_folders: Iterable[Path] = (),
                 main_field: str = 'case'
                 ):
        self.file = file
        self.additional_folders = additional_folders
        self.main_field = main_field
        self._jinja_template = None

    def _ensure_template(self):
        if self._jinja_template is None:
            file = Path(self.file)
            if file.parent != Path('.'):
                parent_folder = [file.parent]
                filename = file.name
            else:
                parent_folder = []
                filename = file.name

            folders = parent_folder + list(self.additional_folders)
            loader = FileSystemLoader(folders)
            env = Environment(loader=loader, autoescape=False)
            self._jinja_template = env.get_template(filename)

    def fill_template_entities(self, case: Any, template_entities: dict):
        template_entities.setdefault(self.main_field, case)

    def fill_arguments(self, case: Any, template_entities: dict, arguments: dict):
        self._ensure_template()
        arguments['prompt'] = self._jinja_template.render(**template_entities)

