from .audio_control_settings import AudioControlSettings
from collections import deque

class MicDataHelper:
    def __init__(self, settings: AudioControlSettings):
        self.settings = settings
        self.buffer = deque()
        self.silent_seconds = 0
        self.recorded_seconds = None

    def reset(self):
        self.buffer = deque()
        self.silent_seconds = 0
        self.recorded_seconds = None

    def recording_started(self):
        self.recorded_seconds = 0

    def observe(self, data, level):
        self.buffer.append(data)
        while len(self.buffer)*self.settings.seconds_in_one_frame > self.settings.silence_margin_in_seconds:
            self.buffer.popleft()
        is_silence = level <= self.settings.silence_level
        if not is_silence:
            self.silent_seconds = 0
        else:
            self.silent_seconds += self.settings.seconds_in_one_frame
        if self.recorded_seconds is not None:
            self.recorded_seconds+=self.settings.seconds_in_one_frame
        return is_silence






