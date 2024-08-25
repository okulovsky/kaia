from ..outputs import RecordingInstance
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

class MicState(Enum):
    Disabled = 0
    Standby = 1
    Open = 2
    Recording = 3

@dataclass
class IterationResult:
    mic_state_before: MicState
    level: float
    playing_before: RecordingInstance | None = None
    playing_now: RecordingInstance | None = None
    produced_file_name: str | None = None
    mic_state_now: MicState = MicState.Disabled


    @property
    def is_significant(self):
        if self.produced_file_name is not None:
            return True
        if self.mic_state_before != self.mic_state_now:
            return True
        if self.playing_before != self.playing_now:
            return True
        return False



@dataclass
class AudioControlLog:
    timestamp: datetime
    iteration_result: IterationResult| None
    exception: str| None

@dataclass
class LevelsLog:
    timestamp: datetime
    level: float


