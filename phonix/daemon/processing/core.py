from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from avatar.messaging import StreamClient, IMessage
from abc import ABC, abstractmethod
from ..inputs import MicData

class MicState(Enum):
    Standby = 0
    Opening = 1
    Open = 2
    Recording = 3
    Sending = 4

@dataclass
class State:
    mic_state: MicState
    update_time: datetime = field(default_factory=datetime.now)

@dataclass
class UnitInput:
    state: State
    mic_data: MicData
    client: StreamClient
    open_mic_requested: bool

class IUnit(ABC):
    @abstractmethod
    def process(self, incoming_data: UnitInput) -> State|None:
        pass

    Input = UnitInput

class SystemSoundType(Enum):
    opening = 0
    confirmation = 1
    error = 2

@dataclass
class SystemSoundCommand(IMessage):
    sound: SystemSoundType
    Type = SystemSoundType


