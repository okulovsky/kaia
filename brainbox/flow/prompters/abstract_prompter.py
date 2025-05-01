from typing import TypeVar, Generic
from abc import ABC, abstractmethod

T = TypeVar('T')

class IPrompter(ABC, Generic[T]):
    @abstractmethod
    def __call__(self, obj: T) -> str:
        pass