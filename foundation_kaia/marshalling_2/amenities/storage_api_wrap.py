from __future__ import annotations
from pathlib import Path
from typing import Iterable, TypeVar, Generic, Callable
from .storage import IStorage, FileDetails, FileLike
import os

T = TypeVar('T')

class StorageApiWrap(Generic[T]):
    def __init__(self, storage: IStorage, key_to_path_prefix: Callable[[T], str]):
        self.inner_api = storage
        self.key_to_path_prefix = key_to_path_prefix

    def _path(self, key: T, path: str | Path) -> str:
        return os.path.join(self.key_to_path_prefix(key), str(path).lstrip('/'))

    def list(self, key: T, path: str | Path, prefix: str | None = None, suffix: str | None = None, glob: bool | None = None) -> list[str]:
        return self.inner_api.list(self._path(key, path), prefix, suffix, glob)

    def list_details(self, key: T, path: str | Path, prefix: str | None = None, suffix: str | None = None, glob: bool | None = None) -> list[FileDetails]:
        return self.inner_api.list_details(self._path(key, path), prefix, suffix, glob)

    def open(self, key: T, filename: str | Path) -> Iterable[bytes]:
        return self.inner_api.open(self._path(key, filename))

    def upload(self, key: T, filename: str | Path, data: FileLike | Iterable[bytes]) -> None:
        return self.inner_api.upload(self._path(key, filename), data)

    def delete(self, key: T, filename: str | Path) -> None:
        return self.inner_api.delete(self._path(key, filename))

    def read_content(self, key: T, filename: str | Path) -> bytes:
        return b''.join(self.open(key, filename))

    def is_file(self, key: T, filename: str | Path) -> bool:
        return self.inner_api.is_file(self._path(key, filename))

    def is_dir(self, key: T, filename: str | Path) -> bool:
        return self.inner_api.is_dir(self._path(key, filename))
