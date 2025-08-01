from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class MicData:
    sample_rate: int
    buffer: list[int]


class IAudioInput(ABC):
    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def stop(self):
        pass

    @abstractmethod
    def read(self) -> MicData:
        pass

    @abstractmethod
    def is_running(self) -> bool:
        pass