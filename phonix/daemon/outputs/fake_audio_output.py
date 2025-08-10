import time
import wave
import io
from typing import Optional
from abc import ABC, abstractmethod
from .audio_output import IAudioOutput


class FakeOutput(IAudioOutput):
    def __init__(self, acceleration: float = 1.0):
        self._acceleration = acceleration
        self._start_time: Optional[float] = None
        self._duration: Optional[float] = None

    def start_playing(self, content: bytes):
        with wave.open(io.BytesIO(content), 'rb') as wav_in:
            frames = wav_in.getnframes()
            framerate = wav_in.getframerate()
            duration = frames / framerate

        self._duration = duration / self._acceleration
        self._start_time = time.monotonic()

    def is_playing(self) -> bool:
        if self._start_time is None or self._duration is None:
            return False
        return (time.monotonic() - self._start_time) < self._duration

    def cancel_playing(self):
        self._start_time = None
        self._duration = None
