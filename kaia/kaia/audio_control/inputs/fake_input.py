from typing import *
from .audio_input import IAudioInput
from io import BytesIO
import wave
import numpy
from pathlib import Path
from yo_fluq import FileIO


class FakeInput(IAudioInput):
    def __init__(self,
                 frame_size: int = 512,
                 ):
        self.frame_size = frame_size
        self.current_buffer: None|numpy.ndarray = None
        self.current_buffer_position = 0

    def set_sample(self, path: Path):
        self.current_buffer = self._content_to_array(FileIO.read_bytes(path))
        self.current_buffer_position = 0

    def _content_to_array(self, wav_file_content: bytes):
        io = BytesIO(wav_file_content)
        wav = wave.open(io, 'r')
        samples = wav.getnframes()
        audio = wav.readframes(samples)
        audio_as_np_int16 = numpy.frombuffer(audio, dtype=numpy.int16)
        return audio_as_np_int16

    def start(self):
        pass

    def stop(self):
        pass

    def is_buffer_empty(self):
        if self.current_buffer is None:
            return True
        return self.current_buffer_position>=len(self.current_buffer)

    def read(self) -> list[int]:
        if self.is_buffer_empty():
            return [0 for _ in range(self.frame_size)]
        chunk = list(self.current_buffer[self.current_buffer_position:self.current_buffer_position+self.frame_size])
        while len(chunk) < self.frame_size:
            chunk.append(0)
        self.current_buffer_position+=len(chunk)
        return chunk

    def is_running(self) -> bool:
        return True

