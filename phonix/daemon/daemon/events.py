from typing import *
from dataclasses import dataclass
from ..processing import MicState
from avatar.messaging import IMessage

@dataclass
class StateChange(IMessage):
    state: MicState

@dataclass
class PlayStarted(IMessage):
    metadata: Any
