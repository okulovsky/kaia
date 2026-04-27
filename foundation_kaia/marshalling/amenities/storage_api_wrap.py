from pathlib import Path
from typing import Iterable, List
from .storage import IStorage, FileDetails, FileLike
import os


class StorageApiWrap(IStorage):
    def __init__(self, storage: IStorage, path_prefix: str):
        self.inner_api = storage
        self.path_prefix = path_prefix

    def _path(self, path: str | Path) -> str:
        return os.path.join(self.path_prefix, str(path).lstrip('/'))

    def list(self, path: str | Path, prefix: str | None = None, suffix: str | None = None, glob: bool | None = None) -> list[str]:
        return self.inner_api.list(self._path(path), prefix, suffix, glob)

    def list_details(self, path: str | Path, prefix: str | None = None, suffix: str | None = None, glob: bool | None = None) -> List[FileDetails]:
        return self.inner_api.list_details(self._path(path), prefix, suffix, glob)

    def open(self, filename: str | Path) -> Iterable[bytes]:
        return self.inner_api.open(self._path(filename))

    def upload(self, filename: str | Path, data: FileLike | Iterable[bytes]) -> None:
        return self.inner_api.upload(self._path(filename), data)

    def delete(self, filename: str | Path) -> None:
        return self.inner_api.delete(self._path(filename))

    def is_file(self, filename: str | Path) -> bool:
        return self.inner_api.is_file(self._path(filename))

    def is_dir(self, filename: str | Path) -> bool:
        return self.inner_api.is_dir(self._path(filename))
