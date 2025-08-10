from avatar import Character, ParaphraseRecord
from brainbox.flow import JinjaPrompter, Prompter
from dataclasses import dataclass
from .jinja_model import JinjaModel
from pathlib import Path
from yo_fluq import FileIO
from uuid import uuid4
from grammatron import Template


@dataclass
class ParaphraseCase:
    model: JinjaModel
    character: Character
    user: Character
    relationship: Prompter|None = None

    pre_existing_templates_count: int = 0
    answer: str|None = None
    result: tuple[Template,...] = ()


    @staticmethod
    def get_paraphrase_template(template: str|None = None):
        if template is None:
            template = FileIO.read_text(Path(__file__).parent/'template.jinja')
        return JinjaPrompter(template)


    def create_paraphrase_record(self, s: str|None):
        if s is not None:
            s = s.strip()
            for symbol in '"*':
                if s.startswith(symbol) and s.endswith(symbol):
                    s = s[1:-1]
            template = self.model.template.restore_template(s)
        else:
            template = None
        return ParaphraseRecord(
            s,
            template,
            self.model.template.template.get_name(),
            self.model.template.variables_tag,
            self.character.name,
            self.user.name,
        )