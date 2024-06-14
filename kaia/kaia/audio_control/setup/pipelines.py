import sys
from typing import *
from ..core import IPipeline, PipelineResult, MicData
from .bufferer import IBuffer, Bufferer
import pvporcupine
import os
from dataclasses import dataclass
from io import BytesIO
import wave, struct

class WavCollectionBuffer(IBuffer):
    def __init__(self, mic_data: MicData):
        self.mic_data = mic_data
        self.wavfile = None

    def _reset(self):
        if self.wavfile is not None:
            self.wavfile.close()
        self.bts = BytesIO()
        self.wavfile = wave.open(self.bts, 'w')
        self.wavfile.setparams((1,2,self.mic_data.sample_rate, self.mic_data.frame_length, "NONE", "NONE"))

    def _write(self, data):
        self.wavfile.writeframes(struct.pack("h"*len(data), *data))

    def start(self, starting_buffer: Iterable[List[int]]):
        self._reset()
        for data in starting_buffer:
            self._write(data)

    def add(self, value: List[int]):
        self._write(value)

    def collect(self):
        self.wavfile.close()
        self.wavfile = None
        return self.bts.getvalue()


class PorcupinePipeline(IPipeline):
    def __init__(self,
                 name: str,
                 confirmation_sound_key: str,
                 follow_up_pipeline: str,
                 ):
        self.name = name
        self.porcupine = pvporcupine.create(keywords=['computer'])
        self.confirmation_sound_key = confirmation_sound_key
        self.follow_up_pipeline = follow_up_pipeline

    def get_name(self) -> str:
        return self.name


    def process(self, data: list[int]) -> PipelineResult | None:
        keyword_index = self.porcupine.process(data)
        if keyword_index >= 0:
            return PipelineResult(None, self.confirmation_sound_key, self.follow_up_pipeline)

    def reset(self) -> None:
        pass


@dataclass
class BuffererPipelineSettings:
    mic_data: MicData
    silence_level: float
    silence_margin_in_seconds: float
    max_length_in_seconds: float
    max_leading_silence_in_seconds: Optional[float]


class BuffererPipeline(IPipeline):
    def __init__(self,
                 name: str,
                 settings: BuffererPipelineSettings,
                 confirmation_sound_key: str,
                 api_call: Callable[[bytes], Any],
                 entering_sound_key: str | None = None,
                 error_sound_key: str | None = None
                 ):
        self.name = name
        self.settings = settings
        self.api_call = api_call
        self.confirmation_sound_key = confirmation_sound_key
        self.bufferer: Bufferer|None = None
        self.entering_sound_key = entering_sound_key
        self.error_sound_key = error_sound_key

    def get_entering_sound_key(self) -> str|None:
        return self.entering_sound_key

    def get_name(self) -> str:
        return self.name

    def reset(self) -> None:
        #print(f'Setting up bufferer {self.name}')
        self.bufferer = Bufferer(
            self.name,
            WavCollectionBuffer(self.settings.mic_data),
            self.settings.silence_level,
            self.settings.mic_data.seconds_to_frames(self.settings.silence_margin_in_seconds),
            self.settings.mic_data.seconds_to_frames(self.settings.max_length_in_seconds),
            None if self.settings.max_leading_silence_in_seconds is None else self.settings.mic_data.seconds_to_frames(self.settings.max_leading_silence_in_seconds)
        )

    def process(self, data: list[int]) -> PipelineResult | None:
        #lv = sum(abs(d) for d in data)/len(data); print(self.name, lv); sys.stdout.flush()
        result = self.bufferer.observe(data)
        if result.wait:
            return None
        if result.error:
            return PipelineResult(None, self.error_sound_key, None)
        #print('Sending request'); sys.stdout.flush()
        recognized = self.api_call(result.result)
        #print('SENT request');sys.stdout.flush()
        return PipelineResult(recognized, self.confirmation_sound_key, None)

    def get_state(self) -> str|None:
        if self.bufferer is None:
            return None
        return self.bufferer.get_state()





