from typing import *
from .narrator import INarrator
from copy import copy

class DummyNarrator(INarrator):
    def __init__(self, default_voice: str):
        self.default_voice = default_voice

    def get_voice(self) -> str:
        return self.default_voice

    def get_image_tags(self) -> dict[str,str]:
        return {}

    def apply_change(self, change: dict[str, str]):
        pass

    def get_state(self) -> dict[str, Any]:
        return {}


class SimpleNarrator(INarrator):
    def __init__(self,
                 main_character: str,
                 voice_dict: dict[str, str],
                 ):
        self.state = dict(character=main_character)
        self.voice_dict = voice_dict

    def get_voice(self) -> str:
        return self.voice_dict[self.state['character']]

    def get_image_tags(self) -> dict[str,str]:
        return copy(self.state)

    def apply_change(self, change: dict[str, str]):
        for key, value in change.items():
            self.state[key] = value

    def get_state(self) -> dict[str, Any]:
        return copy(self.state)
