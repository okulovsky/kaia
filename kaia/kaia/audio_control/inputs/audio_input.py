from abc import ABC, abstractmethod


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