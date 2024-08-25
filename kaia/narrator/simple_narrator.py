from typing import *
from .narrator import INarrator
from .prompts import World
from copy import copy



class SimpleNarrator(INarrator):
    def __init__(self, main_character: None|str):
        self.state = {World.character.field_name:main_character}


    def get_image_tags(self) -> dict[str,str]:
        return copy(self.state)

    def apply_change(self, change: dict[str, str]):
        for key, value in change.items():
            self.state[key] = value

    def get_state(self) -> dict[str, Any]:
        return copy(self.state)
