from .characters import Character
from foundation_kaia.prompters import Referrer

class WorldState:
    user: Character
    character: Character
    activity: str
    language: str

World = Referrer[WorldState]().ref
