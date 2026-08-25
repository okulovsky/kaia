from abc import ABC, abstractmethod
from typing import Iterable
from ...data import Node, Message, IDiff
from ..basic_diffs import Listen

EngineOutput = Listen|Message|IDiff

class IEngine(ABC):
    @abstractmethod
    def generate(self, current: Node) -> Iterable[EngineOutput]:
        pass