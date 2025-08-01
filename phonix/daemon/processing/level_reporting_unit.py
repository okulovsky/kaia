import time

from .core import IUnit
import numpy as np
from .sound_buffer import SoundBuffer
from avatar.messaging import IMessage
from dataclasses import dataclass

@dataclass
class SoundLevel(IMessage):
    level: float

class LevelReportingUnit(IUnit):
    def __init__(self, time_between_reports_in_seconds = 0.05):
        self.time_between_reports_in_seconds = time_between_reports_in_seconds
        self.buffer: SoundBuffer = SoundBuffer(self.time_between_reports_in_seconds)
        self.last_report_time = time.monotonic()

    def process(self, input: IUnit.Input):
        self.buffer.add(input.mic_data)
        t = time.monotonic()
        if t - self.last_report_time > self.time_between_reports_in_seconds:
            self.last_report_time = t
            level = np.mean(np.abs(self.buffer.buffer))/np.iinfo(np.int16).max
            input.client.put(SoundLevel(level))




