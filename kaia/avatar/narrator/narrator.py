from abc import ABC, abstractmethod
from typing import *

class INarrator(ABC):
    @abstractmethod
    def get_voice(self) -> str:
        pass

    @abstractmethod
    def get_image_tags(self) -> dict[str,str]:
        pass

    @abstractmethod
    def apply_change(self, change: dict[str, Any]):
        pass

    @abstractmethod
    def get_state(self) -> dict[str, Any]:
        pass