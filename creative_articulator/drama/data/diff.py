from ...common import Node
from abc import ABC, abstractmethod

class IDiff(ABC):
    @abstractmethod
    def apply(self, root: Node):
        pass


class DiffList(list[IDiff]):
    pass



