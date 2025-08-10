from typing import List, Optional
from ..inputs import MicData

class SoundBuffer:
    def __init__(self, max_time_seconds: float):
        """
        Audio sample buffer with a time-based size limit.

        :param max_time_seconds: maximum buffer length in seconds
        """
        self.max_time_seconds = max_time_seconds
        self.sample_rate: Optional[int] = None
        self.buffer: List[int] = []
        self.is_full = False

    def clear(self):
        self.buffer.clear()
        self.is_full = False

    def add(self, data: MicData) -> None:
        sample_rate = data.sample_rate
        samples = data.buffer
        """
        Add a block of samples to the buffer.
        If the sample rate has changed, the buffer is cleared.

        :param sample_rate: sample rate of the incoming samples
        :param samples: list of new samples (int)
        """
        # Reset buffer if sample rate changes
        if self.sample_rate is None or self.sample_rate != sample_rate:
            self.sample_rate = sample_rate
            self.clear()


        # Append new samples
        self.buffer.extend(samples)

        # Trim buffer to the max allowed samples
        max_samples = int(self.max_time_seconds * self.sample_rate)
        if len(self.buffer) > max_samples:
            # Keep only the most recent samples
            self.buffer = self.buffer[-max_samples:]
            self.is_full = True