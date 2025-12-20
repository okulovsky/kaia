from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Iterable, Callable, TYPE_CHECKING
import ipywidgets

if TYPE_CHECKING:
    from .drawer import Drawer

class IDrawable(ABC):
    @abstractmethod
    def to_html(self) -> str:
        ...

    @abstractmethod
    def to_widget(self) -> ipywidgets.Widget:
        ...

    def draw(self) -> 'Drawer':
        from .drawer import Drawer
        return Drawer(self)

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


class IDrawableCollection(ABC):
    @abstractmethod
    def get_drawables(self) -> Iterable[IDrawable]:
        ...

    def draw(self) -> 'Drawer':
        from .drawer import Drawer
        return Drawer(self)

    def assign_metakey(self, key: str, value: str) -> None:
        for drawable in self.get_drawables():
            drawable.assign_metakey(key, value)

    def assign_metadata(self, **kwargs) -> None :
        for key, value in kwargs.items():
            self.assign_metakey(key, value)


