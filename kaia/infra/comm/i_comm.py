from abc import ABC, abstractmethod
from .i_messenger import IMessenger
from .i_storage import IStorage

class IComm(ABC):
    @abstractmethod
    def messenger(self) -> IMessenger:
        pass

    @abstractmethod
    def storage(self) -> IStorage:
        pass