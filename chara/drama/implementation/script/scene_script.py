from dataclasses import dataclass
from ..scene import Medium
from brainbox.flow import JinjaPrompter
from .file_manager import FileManager

@dataclass
class SceneScript:
    intro: JinjaPrompter[dict[str,str]]
    goal: JinjaPrompter[dict[str,str]]
    medium: Medium
    length: int
    length_strict: bool
    roles: tuple[str,...]

    @staticmethod
    def parse_scenes(manager: FileManager):
        result = []
        for data in manager.parse_yaml(manager.sections['Scenes']):
            intro = JinjaPrompter(data['intro'])
            goal = JinjaPrompter(data['goal']) if 'goal' in data else None
            medium = Medium[data.get("medium", Medium.default.name)]
            length = int(data.get('length', 10))
            roles = intro.get_variables()
            length_strict = data.get('length_strict', False) != False
            result.append(SceneScript(intro, goal, medium, length, length_strict, roles))
        return result