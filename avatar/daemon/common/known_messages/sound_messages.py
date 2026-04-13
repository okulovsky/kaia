from ....messaging import IMessage
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum


@dataclass
class SetSilenceLevelCommand(IMessage):
    level: float = 0.1

@dataclass
class SoundLevelReport(IMessage):
    decision_level: float | None
    silence_level: float
    begin_timestamp: datetime
    end_timestamp: datetime
    levels: list[float]



@dataclass
class SoundCommand(IMessage):
    file_id: str
    text: str|None = None


@dataclass
class SoundConfirmation(IMessage):
    terminated: bool = False
    error: str | None = None


@dataclass
class SoundEvent(IMessage):
    file_id: str


@dataclass
class SoundStreamingStartEvent(IMessage):
    file_id: str

@dataclass
class SoundStreamingEndEvent(IMessage):
    file_id: str
    success: bool




@dataclass
class SoundInjectionCommand(IMessage):
    file_id: str


@dataclass
class SoundInjectionStartedEvent(IMessage):
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
