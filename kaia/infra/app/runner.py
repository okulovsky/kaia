from abc import ABC, abstractmethod

class IRunner(ABC):
    @abstractmethod
    def run(self):
        pass

    @abstractmethod
    def stop(self):
        pass

