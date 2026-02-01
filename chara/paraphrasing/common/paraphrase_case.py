from dataclasses import dataclass, field
from chara.common import Character
from .parsed_template import ParsedTemplate
from uuid import uuid4

@dataclass(frozen=True)
class ParaphraseFingerprint:
    original_template_name: str
    variables_tag: str
    language: str
    character_name: str
    user_name: str|None = None



@dataclass
class ParaphraseCase:
    template: ParsedTemplate
    language: str = 'en'
    character: Character|None = None
    user: Character|None = None
    relationship: str|None = None

    def get_fingerprint(self) -> ParaphraseFingerprint:
        return ParaphraseFingerprint(
            self.template.template.get_name(),
            self.template.variables_tag,
            self.language,
            None if self.character is None else self.character.name,
            None if self.user is None else self.user.name
        )


