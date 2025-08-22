import time
from .core import IUnit
import numpy as np
from .sound_buffer import SoundBuffer
from avatar.messaging import IMessage
from dataclasses import dataclass, field
from datetime import datetime



@dataclass
class SoundLevelReport(IMessage):
    begin_timestamp: datetime
    end_timestamp: datetime|None = None
    levels: list[float]=field(default_factory=list)


class LevelReportingUnit(IUnit):
    def __init__(self, time_between_reports_in_seconds: float = 1, discretization_in_seconds: float = 0.05):
        self.time_between_reports_in_seconds = time_between_reports_in_seconds
        self.buffer: SoundBuffer = SoundBuffer(0.05)
        self.current_report = SoundLevelReport(datetime.now())

    def process(self, input: IUnit.Input):
        t = datetime.now()
        delta = (t-self.current_report.begin_timestamp).total_seconds()
        self.buffer.add(input.mic_data)
        if self.buffer.is_full:
            level = np.mean(np.abs(self.buffer.buffer)) / np.iinfo(np.int16).max
            input.monitor.on_level(level)
            self.current_report.levels.append(level)
            self.buffer.clear()
        if delta > self.time_between_reports_in_seconds:
            self.current_report.end_timestamp = datetime.now()
            input.send_message(self.current_report)
            self.current_report = SoundLevelReport(datetime.now())




