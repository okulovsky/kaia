from yo_fluq import FileIO
from pathlib import Path
from foundation_kaia.prompters import JinjaPrompter
from ..common import ParaphraseCase
from .jinja_model import JinjaModel
from typing import TypeVar

T = TypeVar("T")

class ParaphrasingPrompter:
    def __init__(self, custom_template_path: Path|None = None):
        path = Path(__file__).parent/'template.jinja'
        if custom_template_path is not None:
            path = custom_template_path

        template_text = FileIO.read_text(path)
        self.template = JinjaPrompter(template_text)

    def __call__(self, element: ParaphraseCase):
        model = JinjaModel.build_from_case(element)
        prompt = self.template(model)
        return prompt
