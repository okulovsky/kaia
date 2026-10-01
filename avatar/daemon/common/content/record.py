from abc import ABC, abstractmethod
from typing import Any


class IRecord(ABC):
    @abstractmethod
    def get_id(self) -> str:
        pass

    @abstractmethod
    def get_tags(self) -> dict[str, Any]:
        pass
