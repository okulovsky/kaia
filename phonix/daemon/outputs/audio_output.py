from abc import ABC, abstractmethod

class IAudioOutput(ABC):
    @abstractmethod
    def start_playing(self, content: bytes):
        pass

    @abstractmethod
    def is_playing(self) -> bool:
        pass

    @abstractmethod
    def cancel_playing(self):
        pass
