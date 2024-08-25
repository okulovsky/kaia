import time
from dataclasses import dataclass
from pathlib import Path
from enum import Enum
from abc import ABC, abstractmethod

@dataclass
class Recording:
    content: bytes
    title: None | str = None

    @staticmethod
    def from_file(path: Path|str):
        path = Path(path)
        with open(path, 'rb') as stream:
            return Recording(stream.read(), path.name)

    def to_instance(self):
        return RecordingInstance(self)


@dataclass
class RecordingInstance:
    class State(Enum):
        Waiting = 0
        Playing = 1
        Finished = 2

    recording: Recording
    internal: bool = False
    state: 'RecordingInstance.State' = State.Waiting


class IAudioOutput(ABC):
    @abstractmethod
    def start_playing(self, sample: RecordingInstance):
        pass

    @abstractmethod
    def what_is_playing(self) -> RecordingInstance|None:
        pass

    @abstractmethod
    def set_volume(self, volume: float):
        pass

    def play_and_wait(self, sample: bytes|Recording|RecordingInstance):
        if isinstance(sample, bytes):
            sample = Recording(sample).to_instance()
        elif isinstance(sample, Recording):
            sample = sample.to_instance()
        self.start_playing(sample)
        while self.what_is_playing() is not None:
            time.sleep(0.1)

