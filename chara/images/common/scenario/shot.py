from dataclasses import dataclass
from typing import ClassVar

from .image_scenario import assemble_tags


@dataclass
class Framing:
    text: str|None
    legs_visible: bool
    feet_visible: bool

@dataclass
class CharacterAngle:
    text: str|None
    is_back_view: bool
    is_front_view: bool


@dataclass
class Shot:
    framing: Framing|None = None
    character_angle: CharacterAngle|None = None
    camera_angle: str|None = None

    Framing: ClassVar = Framing
    CharacterAngle: ClassVar = CharacterAngle

    @property
    def is_back_view(self):
        return self.character_angle.is_back_view

    @property
    def is_front_view(self):
        return self.character_angle.is_front_view

    @property
    def legs_visible(self):
        return self.framing.legs_visible

    @property
    def feet_visible(self):
        return self.framing.feet_visible

    def to_prompt(self):
        return assemble_tags(
            self.framing.text if self.framing else None,
            self.character_angle.text if self.character_angle else None,
            self.camera_angle,
        )


