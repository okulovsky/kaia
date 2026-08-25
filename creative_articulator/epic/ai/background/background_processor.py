from abc import ABC, abstractmethod
from typing import Any
from ....common import Node


class IBackgroundProcessor(ABC):
    @abstractmethod
    def prepare(self, node: Node) -> Any:
        pass

    @abstractmethod
    def execute(self, task: Any) -> Any:
        pass

    @abstractmethod
    def apply(self, node: Node, task: Any, result: Any) -> None:
        pass

