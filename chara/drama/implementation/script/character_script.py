from dataclasses import dataclass
from brainbox.flow import JinjaPrompter
from ..scene import Medium
from .file_manager import FileManager

@dataclass
class CharacterScript:
    name: str
    description: str
    style: dict[Medium, str]|None = None

    def get_style(self, medium: Medium):
        if self.style is None:
            return ''
        if medium not in self.style:
            return self.style[Medium.default]
        return self.style[medium]

    @staticmethod
    def parse_one_character(character_data) -> 'CharacterScript':
        c = CharacterScript(character_data['name'], None)
        c.description = JinjaPrompter(character_data['description'])(c)
        if 'style' in character_data:
            if isinstance(character_data['style'], str):
                c.style = {Medium.default: JinjaPrompter(character_data['style'])(c)}
            else:
                c.style = {Medium[k]: JinjaPrompter(v)(c) for k, v in character_data['style'].items()}
        return c

    @staticmethod
    def parse_characters(manager: FileManager) -> dict[str, 'CharacterScript']:
        data = manager.parse_yaml(manager.sections['Characters'])
        result = {}
        for role, spec in data.items():
            if isinstance(spec, str):
                result[role] = manager.predefined_characters[spec]
            else:
                result[role] = CharacterScript.parse_one_character(spec)
        return result

