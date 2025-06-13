from .character import Character
from brainbox.flow import Referrer

class WorldState:
    user: Character
    character: Character
    activity: str
    language: str

World = Referrer[WorldState]().ref

class WorldFields:
    character = 'character'
    user = 'user'
    activity = 'activity'
    language = 'language'