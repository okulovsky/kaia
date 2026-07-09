from dataclasses import dataclass
from typing import Any
from ...messaging import IMessage
from .music_player import MusicStatus

@dataclass
class MusicStopButtonEvent(IMessage):
    pass

@dataclass
class MusicPauseButtonEvent(IMessage):
    pass

@dataclass
class MusicResumeButtonEvent(IMessage):
    pass

@dataclass
class MusicNextButtonEvent(IMessage):
    pass

@dataclass
class MusicPreviousButtonEvent(IMessage):
    pass

@dataclass
class MusicStartCommand(IMessage):
    id: Any

@dataclass
class MusicStatusCommand(IMessage):
    status: MusicStatus