from abc import ABC, abstractmethod
from typing import Iterable, Tuple, Any


class INodeStorage(ABC):
    @abstractmethod
    def has(self, key: type) -> bool:
        pass

    @abstractmethod
    def get(self, key: type) -> Any:
        pass

    @abstractmethod
    def set(self, key: type, value):
        pass


    @abstractmethod
    def items(self) -> Iterable[Tuple[Any, Any]]:
        pass

    @abstractmethod
    def commit(self, key: type):
        pass

    @abstractmethod
    def rollback(self, key: type):
        pass

    @abstractmethod
    def delete(self, key: type):
        pass
