from abc import ABC, abstractmethod
from typing import Any
from ..common import State


class INarrator(ABC):
    @abstractmethod
    def update_character(self, state: State, character: str|None = None) -> str|None:
        pass

    @abstractmethod
    def update_activity(self, state: State) -> list[Any]:
        pass

    @abstractmethod
    def initialize(self, state: State) -> list[Any]:
        pass

    @abstractmethod
    def regular_update(self, state: State) -> list[Any]:
        pass
