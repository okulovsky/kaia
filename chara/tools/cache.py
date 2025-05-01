from typing import Any, TypeVar, Generic
import requests
from abc import ABC, abstractmethod
from pathlib import Path
from yo_fluq import FileIO


class ICacheManager(ABC):
    def save(self, data: dict[tuple[str,...], Any]):
        pass

    def load(self) -> dict[tuple[str,...], Any]:
        pass

class JsonCacheManager(ICacheManager):
    def __init__(self, path: Path|str):
        self.path = Path(path)

    def save(self, data: dict[tuple[str,...], Any]):
        new_data = []
        for key, value in data.items():
            new_data.append(dict(key=list(key), value=value))
        FileIO.write_json(new_data, self.path)

    def load(self):
        if self.path.is_file():
            data = FileIO.read_json(self.path)
        else:
            data = {}
        return {tuple(item['key']):item['value'] for item in data}

class ICacheInstance(ABC):
    @abstractmethod
    def query(self, *keys):
        pass

    @property
    def data(self) -> dict[tuple[str,...], Any]:
        if hasattr(self,'_data'):
            return self._data
        else:
            return {}

    @data.setter
    def data(self, value: dict[tuple[str,...], Any]):
        self._data = value

    def _get_internal(self, *keys):
        data = self.data
        if keys not in data:
            data[keys] = self.query(*keys)
        return data[keys]

T = TypeVar("T")

class Cache(Generic[T]):
    def __init__(self, cache_manager: ICacheManager, instance_factory):
        self.cache_manager = cache_manager
        self.instance_factory = instance_factory
        self._returned_instance: ICacheInstance|None = None

    def __enter__(self) -> T:
        data = self.cache_manager.load()
        self._returned_instance = self.instance_factory()
        self._returned_instance.data = data
        return self._returned_instance

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._returned_instance is not None:
            self.cache_manager.save(self._returned_instance.data)


    Instance = ICacheInstance