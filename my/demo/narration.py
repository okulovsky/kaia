from typing import *
from kaia.avatar.narrator import INarrator
from copy import copy

characters = ['Jug', 'Lina']

class Narrator(INarrator):
    def __init__(self):
        self.state = dict(character=characters[0])

    def get_state(self) -> dict[str, Any]:
        return copy(self.state)

    def get_image_tags(self) -> dict[str,str]:
        return dict(character=self.state['character'])

    def get_voice(self) -> str:
        if self.state['character'] == 'Lina':
            return 'p225'
        else:
            return 'p229'



    def apply_change(self, change: dict[str, Any]):
        for key, value in change.items():
            self.state[key] = value


def create_narrator():
    return Narrator()
