from dataclasses import dataclass
from ...messaging import IMessage


@dataclass
class State(IMessage):
    character: str|None = None
    activity: str|None = None
    language: str|None = None
    time_of_day: str|None = None
    season: str|None = None
    weather: str|None = None
    special_day: str|None = None
