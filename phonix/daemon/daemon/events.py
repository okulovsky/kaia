from typing import *
from dataclasses import dataclass
from ..processing import MicState
from avatar.messaging import IMessage

@dataclass
class MicStateChangeReport(IMessage):
    state: MicState

@dataclass
class SoundPlayStarted(IMessage):
    metadata: Any
