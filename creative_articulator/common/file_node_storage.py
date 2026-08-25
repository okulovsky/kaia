from typing import Any, Iterable, Tuple

from .node_storage import INodeStorage
from .memory_node_storage import MemoryNodeStorage
from avatar.app.messages.aliases_discovery import create_aliases
from chara.common.architecture.file_handling import FolderHandler
from pathlib import Path

class FileNodeStorage(INodeStorage):
    def __init__(self, base_folder: Path, namespaces: tuple[str, ...] = ()) -> None:
        self._handler = FolderHandler(base_folder)
        self._aliases = create_aliases(namespaces, base_class=object)
        self._loaded: MemoryNodeStorage = MemoryNodeStorage()
        self._memory_only = set[type]()


    def _name(self, key: type):
        return key.__name__.split('.')[-1]

    def _is_memory_only(self, key):
        return key in self._memory_only

    def has(self, key: type) -> bool:
        if self._loaded.has(key):
            return True
        if self._is_memory_only(key):
            return False
        return self._handler.has_file(self._name(key))

    def get(self, key: type) -> Any:
        if self._loaded.has(key):
            return self._loaded.get(key)
        if self._is_memory_only(key):
            raise KeyError(key)
        value = self._handler.read(self._name(key))
        self._loaded.set(key, value)
        return value

    def set(self, key: type, value):
        self._loaded.set(key, value)
        if not self._is_memory_only(key):
            self._handler.write(self._name(key), value)


    def items(self) -> Iterable[Tuple[Any, Any]]:
        for path in self._handler.folder.iterdir():
            key = self._aliases.get(path.stem)
            if key is None:
                raise ValueError(f"File {path.stem} does not correspond to any known type")
            # A file left over from before the key became memory-only: the
            # in-memory value is the only truth now, so the file is ignored
            # here instead of being read back over it.
            if self._is_memory_only(key):
                continue
            value = self._handler.read(self._name(key))
            self._loaded.set(key, value)
            yield key, value
        for key, value in self._loaded.items():
            if self._is_memory_only(key):
                yield key, value

    def commit(self, key: type):
        if not self._is_memory_only(key):
            self._handler.write(self._name(key), self._loaded.get(key))

    def rollback(self, key: type):
        # A memory-only key has no file to restore from, so a session over one
        # keeps whatever the failed block managed to write - same as
        # MemoryNodeStorage. Only use sessions on keys that are persisted.
        if not self._is_memory_only(key):
            self._loaded.set(key, self._handler.read(self._name(key)))

    def memory_only(self, key: type):
        self._memory_only.add(key)

    def delete(self, key: type):
        self._loaded.delete(key)
        if not self._is_memory_only(key):
            path = self._handler.get_file(self._name(key))
            if path is not None:
                path.unlink()

