from abc import ABC, abstractmethod
from datetime import datetime
from ..common import State


class IStateFieldSetter(ABC):
    @abstractmethod
    def update(self, state: State, now: datetime) -> None:
        pass
