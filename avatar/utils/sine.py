import io
import wave
import struct
import math
from pathlib import Path

class Sine:
    def __init__(self, sample_rate: int = 22050):
        self._sample_rate = sample_rate
        self._buffer = io.BytesIO()
        self._writer = wave.open(self._buffer, 'wb')
        self._writer.setnchannels(1)
        self._writer.setsampwidth(2)
        self._writer.setframerate(sample_rate)

    def segment(self, amplitude: float, duration_seconds: float = 2.0) -> 'Sine':
        if amplitude < 0 or amplitude > 1:
            raise ValueError('amplitude must be between 0 and 1')
        n = int(self._sample_rate * duration_seconds)
        self._writer.writeframes(struct.pack(f'<{n}h', *[
            int(amplitude * (math.pi / 2) * 32767 * math.sin(2 * math.pi * 440 * i / self._sample_rate))
            for i in range(n)
        ]))
        return self

    def append(self, wav_file: Path) -> 'Sine':
        #TODO: append this wav file if the sample_rate matches, throw otherwise
        return self
        pass


    def bytes(self) -> bytes:
        self._writer.close()
        return self._buffer.getvalue()
