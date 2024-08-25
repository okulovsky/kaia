from abc import ABC, abstractmethod

class IWakeWordDetector(ABC):
    @abstractmethod
    def detect(self, data: list[int]) -> bool:
        pass
