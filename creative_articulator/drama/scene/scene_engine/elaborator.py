from abc import ABC, abstractmethod
from typing import Iterable
from ...data import Node, IDiff

class IElaborator(ABC):
    @abstractmethod
    def elaborate(self, node: Node) -> Iterable[IDiff]:
        pass

