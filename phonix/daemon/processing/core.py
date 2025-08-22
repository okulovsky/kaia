from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from avatar.messaging import StreamClient, IMessage
from abc import ABC, abstractmethod
from ..inputs import MicData
from typing import Callable


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


class IMonitor:
    def on_level(self, level: float):
        pass

    def on_silence_level(self, silence_level: float):
        pass

    def on_state_change(self, new_state: State):
        pass


@dataclass
class UnitInput:
    state: State
    mic_data: MicData
    received_messages: tuple[IMessage,...]
    open_mic_requested: bool
    monitor: IMonitor
    send_message: Callable[[IMessage],None]


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


