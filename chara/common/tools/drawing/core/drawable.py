from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import TypeVar, Generic


class IDrawable(ABC):
    @abstractmethod
    def to_html(self) -> str:
        pass

    @property
    def metadata(self) -> dict:
        if not hasattr(self, '_metadata'):
            self._metadata = {}
        return self._metadata

    def assign_metakey(self, key: str, value: str) -> None:
        self.metadata[key] = value

    def assign_metadata(self, **kwargs) -> None :
        for key, value in kwargs.items():
            self.assign_metakey(key, value)

T = TypeVar('T', bound=IDrawable)


class IDrawableCollection(Iterable[T], Generic[T]):
    def assign_metakey(self, key: str, value: str) -> None:
        for drawable in self:
            drawable.assign_metakey(key, value)

    def assign_metadata(self, **kwargs) -> None :
        for key, value in kwargs.items():
            self.assign_metakey(key, value)