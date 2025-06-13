from avatar import Character, ParaphraseRecord
from brainbox.flow import JinjaPrompter, Prompter
from dataclasses import dataclass
from .paraphrase_info import ParaphraseInfo
from pathlib import Path
from yo_fluq import FileIO
from uuid import uuid4


@dataclass
class ParaphraseCase:
    info: ParaphraseInfo
    character: Character
    user: Character
    relationship: Prompter|None = None

    @staticmethod
    def get_paraphrase_template(template: str|None = None):
        if template is None:
            template = FileIO.read_text(Path(__file__).parent/'template.jinja')
        return JinjaPrompter(template)



    def create_paraphrase_record(self, s: str):
        s = s.strip()
        for symbol in '"*':
            if s.startswith(symbol) and s.endswith(symbol):
                s = s[1:-1]
        return ParaphraseRecord(
            str(uuid4()),
            self.info.restore_template(s),
            self.info.template_name,
            ParaphraseRecord.create_variables_tag(self.info.variables),
            self.character.name,
            self.user.name,
        )