from ....messaging import IMessage
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum


@dataclass
class SetSilenceLevelCommand(IMessage):
    level: float = 0.1


@dataclass
class SoundLevelReport(IMessage):
    begin_timestamp: datetime
    end_timestamp: datetime|None = None
    levels: list[float] = field(default_factory=list)
    silence_level: float = 0.1


@dataclass
class SoundCommand(IMessage):
    file_id: str
    text: str|None = None


@dataclass
class SoundConfirmation(IMessage):
    terminated: bool = False


@dataclass
class SoundEvent(IMessage):
    file_id: str


@dataclass
class SoundStartEvent(IMessage):
    file_id: str


@dataclass
class SoundInjectionCommand(IMessage):
    file_id: str


@dataclass
class VolumeCommand(IMessage):
    value: float


@dataclass
class VolumeEvent(IMessage):
    value: float


@dataclass
class WakeWordEvent(IMessage):
    word: str|None = None


@dataclass
class OpenMicCommand(IMessage):
    pass


class StatefulRecorderState(str, Enum):
    Standby = 'Standby'
    Open = 'Open'
    Record = 'Record'
    Commit = 'Commit'
    Cancel = 'Cancel'


@dataclass
class StatefulRecorderStateCommand(IMessage):
    state: StatefulRecorderState


@dataclass
class StatefulRecorderStateEvent(IMessage):
    state: StatefulRecorderState


@dataclass
class SystemSoundCommand(IMessage):
    sound_name: str  # maps to frontend/system-sounds/{sound_name}.wav
