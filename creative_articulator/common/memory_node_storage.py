from typing import Iterable, Tuple, Any
from .node_storage import INodeStorage

class MemoryNodeStorage(INodeStorage):
    def __init__(self):
        self._storage = {}

    def has(self, key) -> bool:
        return key in self._storage

    def get(self, key) -> Any:
        return self._storage[key]

    def set(self, key, value):
        self._storage[key] = value

    def items(self) -> Iterable[Tuple[Any, Any]]:
        return self._storage.items()

    def commit(self, key: type):
        pass

    def rollback(self, key: type):
        pass

    def delete(self, key: type):
        self._storage.pop(key, None)