import time
from .core import IUnit
import numpy as np
from .sound_buffer import SoundBuffer
from avatar.messaging import IMessage
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class SoundLevelReportItem:
    delta: float
    value: float


@dataclass
class SoundLevelReport(IMessage):
    begin_timestamp: datetime
    levels: list[SoundLevelReportItem] = field(default_factory=list)


class LevelReportingUnit(IUnit):
    def __init__(self, time_between_reports_in_seconds: float = 0.5):
        self.time_between_reports_in_seconds = time_between_reports_in_seconds
        self.buffer: SoundBuffer = SoundBuffer(0.05)
        self.current_report = SoundLevelReport(datetime.now())


    def process(self, input: IUnit.Input):
        t = datetime.now()
        delta = (t-self.current_report.begin_timestamp).total_seconds()
        self.buffer.add(input.mic_data)
        if self.buffer.is_full:
            level = np.mean(np.abs(self.buffer.buffer)) / np.iinfo(np.int16).max
            self.current_report.levels.append(SoundLevelReportItem(delta, level))
            self.buffer.clear()
        if delta > self.time_between_reports_in_seconds:
            input.client.put(self.current_report)
            self.current_report = SoundLevelReport(datetime.now())




