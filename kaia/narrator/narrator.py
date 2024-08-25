from abc import ABC, abstractmethod
from typing import *

class INarrator(ABC):
    @abstractmethod
    def apply_change(self, change: dict[str, Any]):
        pass

    @abstractmethod
    def get_state(self) -> dict[str, Any]:
        pass