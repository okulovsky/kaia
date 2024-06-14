from typing import *
from dataclasses import dataclass
from abc import ABC, abstractmethod
import math
from enum import Enum
from pathlib import Path


@dataclass
class AudioSampleTemplate:
    content: bytes
    title: None | str = None

    @staticmethod
    def from_file(path: Path|str):
        path = Path(path)
        with open(path, 'rb') as stream:
            return AudioSampleTemplate(stream.read(), path.name)

    def to_sample(self):
        return AudioSample(self)

@dataclass
class AudioSample:
    class State(Enum):
        Waiting = 0
        Playing = 1
        Finished = 2

    template: AudioSampleTemplate
    internal: bool = False
    state: 'AudioSample.State' = State.Waiting


class IAudioOutput(ABC):
    @abstractmethod
    def start_playing(self, sample: AudioSample):
        pass

    @abstractmethod
    def what_is_playing(self) -> AudioSample|None:
        pass

    @abstractmethod
    def set_volume(self, volume: float):
        pass


class IAudioInput(ABC):
    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def stop(self):
        pass

    @abstractmethod
    def read(self) -> list[int]:
        pass

    @abstractmethod
    def is_running(self) -> bool:
        pass


@dataclass
class PipelineResult:
    collected_data: Any
    play_sound: Any
    next_state: str | None


class IPipeline(ABC):
    @abstractmethod
    def process(self, data: list[int]) -> PipelineResult | None:
        pass

    @abstractmethod
    def reset(self) -> None:
        pass

    @abstractmethod
    def get_name(self) -> str:
        pass

    def get_entering_sound_key(self) -> str|None:
        return None

    def get_state(self) -> str|None:
        return None



@dataclass
class IterationResult:
    from_state: str
    to_state: str
    audio_sample_playing: AudioSample | None
    audio_sample_started: AudioSample | None
    audio_sample_finished: AudioSample | None
    processed_input: PipelineResult | None

    def is_empty(self):
        return (
                self.audio_sample_finished is None and
                self.audio_sample_started is None and
                self.processed_input is None
        )


@dataclass
class MicData:
    sample_rate: int
    frame_length: int

    def seconds_to_frames(self, seconds: float) -> int:
        return int(math.ceil(seconds*self.sample_rate/self.frame_length))
