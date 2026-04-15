from __future__ import annotations
from queue import Queue
from typing import TYPE_CHECKING
from abc import ABC, abstractmethod

if TYPE_CHECKING:
    from .core import Core

class ICoreAction(ABC):
    @abstractmethod
    def apply(self, core: Core):
        pass

class CommandQueue(Queue):
    def put_action(self, action: ICoreAction) -> None:
        self.put(action)
