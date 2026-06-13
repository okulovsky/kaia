from copy import deepcopy
from dataclasses import dataclass
from chara.common import Character
from pathlib import Path
from ...common import IImageScenario, assemble_tags, TextToImage
from .clothing import Clothing
from typing import Any

@dataclass
class Scene:
    position: tuple[str,...]
    environment: tuple[str,...]

    def to_prompt(self):
        return assemble_tags(
            self.position,
            self.environment
        )

    def all_tags_str(self) -> str:
        return ", ".join(self.position + self.environment)


@dataclass
class Shot:
    framing: str|None = None
    character_angle: str|None = None
    camera_angle: str|None = None

    def to_prompt(self):
        return assemble_tags(
            self.framing,
            self.character_angle,
            self.camera_angle,
        )


@dataclass
class Theme:
    name: str
    description: str|None = None

    @property
    def full_text(self) -> str:
        result = self.name
        if self.description is not None:
            result+= ' ('+self.description+')'
        return result

@dataclass(kw_only=True)
class ImageContext:
    template: TextToImage
    positive_prompt: str|None = None
    negative_prompt: str | None = None
    name_to_keyword_template: str|None = None
    name_to_lora_file_template: str|None = None



@dataclass
class ImageScenarioCase(IImageScenario):
    context: ImageContext
    character: Character

    theme: Theme|None = None
    activity: str|None = None
    activity_tags: tuple[str,...]|None = None

    scene: Scene|None = None
    shot: Shot|None = None
    clothing: Clothing|None = None
    face: str|None = None
    other_tags: str|None = None

    workflow: Any = None
    image: Path|None = None
    self_review: Any = None

    def get_other_tags(self) -> str|None:
        return self.other_tags

    def get_positive_prompt(self) -> str:
        return assemble_tags(
            self.context.name_to_keyword_template.format(self.character.name),
            self.context.positive_prompt,
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
            self.context.negative_prompt,
            self.character.appearance.negative_prompt
        )

    def to_workflow(self) -> TextToImage:
        result = deepcopy(self.context.template)
        result.prompt = self.get_positive_prompt()
        result.negative_prompt = self.get_negative_prompt()
        if self.context.name_to_lora_file_template is not None:
            result.lora_01 = self.context.name_to_lora_file_template.format(self.character.name)
        return result




