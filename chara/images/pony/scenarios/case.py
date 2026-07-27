from copy import deepcopy
from dataclasses import dataclass
from chara.common import Character
from brainbox.deciders.images.comfyui.workflows import TextToImage
from ...common import IImageScenario, assemble_tags, Theme, Clothing, Shot, Scene
from .settings import PonySettings

@dataclass
class PonyCase(IImageScenario):
    character: Character
    settings: PonySettings

    theme: Theme|None = None
    activity: str|None = None
    activity_tags: tuple[str,...]|None = None

    scene: Scene|None = None
    shot: Shot|None = None
    clothing: Clothing|None = None
    face: str|None = None
    other_tags: str|None = None

    def get_other_tags(self) -> str|None:
        return self.other_tags

    def get_positive_prompt(self) -> str:
        return assemble_tags(
            self.settings.name_to_keyword_template.format(self.character.name),
            self.settings.positive_prompt,
            self.character.appearance.positive_prompt,
            self.activity,
            self.scene.to_prompt() if self.scene else None,
            self.clothing.to_prompt() if self.clothing else None,
            self.face,
            self.shot.to_prompt() if self.shot else None,
            self.get_other_tags()
        )

    def get_negative_prompt(self) -> str:
        return assemble_tags(
            self.settings.negative_prompt,
            self.character.appearance.negative_prompt
        )

    def to_workflow(self) -> TextToImage:
        result = deepcopy(self.settings.template)
        result.prompt = self.get_positive_prompt()
        result.negative_prompt = self.get_negative_prompt()
        if self.settings.name_to_lora_file_template is not None:
            result.lora_01 = self.settings.name_to_lora_file_template.format(self.character.name)
        return result
