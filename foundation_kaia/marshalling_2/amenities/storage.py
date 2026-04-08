from __future__ import annotations

import os
import shutil
from abc import ABC
from ..marshalling import endpoint, service, FileLike, File, FileLikeHandler, ApiCall
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

@dataclass
class FileDetails:
    name: str
    last_modification_date: datetime

@service
class IStorage(ABC):
    @endpoint(is_pathlike='path')
    def list(self, path: str|Path, prefix: str|None = None, suffix: str|None = None, glob: bool|None = None) -> list[str]:
        ...

    @endpoint(is_pathlike='path')
    def list_details(self, path: str|Path, prefix: str|None = None, suffix: str|None = None, glob: bool|None = None) -> list[FileDetails]:
        ...

    @endpoint(is_pathlike='filename', method='GET')
    def open(self, filename: str|Path) -> Iterable[bytes]:
        ...

    @endpoint(is_pathlike='filename')
    def upload(self, filename: str|Path, data: FileLike|Iterable[bytes]) -> None:
        ...

    @endpoint(is_pathlike='filename')
    def delete(self, filename: str|Path) -> None:
        ...

    @endpoint(is_pathlike='filename')
    def is_file(self, filename: str|Path) -> bool:
        ...

    @endpoint(is_pathlike='filename')
    def is_dir(self, filename: str|Path) -> bool:
        ...

    def read(self, filename: str|Path) -> bytes:
        return b''.join(self.open(filename))

    def download(self, filename: str|Path, target_folder: Path) -> Path:
        target = target_folder / Path(filename).name
        target.write_bytes(self.read(filename))
        return target

    def read_file(self, filename: str|Path) -> File:
        return File(Path(filename).name, self.read(filename))





class Storage(IStorage):
    def __init__(self, folder: Path):
        self.folder = folder

    def _iter_files(self, full_path: Path, prefix: str|None, suffix: str|None, glob: bool|None) -> list[Path]:
        iterator = full_path.rglob('*') if glob else full_path.iterdir()
        result = []
        for f in iterator:
            if not f.is_file():
                continue
            name = f.name
            if prefix is not None and not name.startswith(prefix):
                continue
            if suffix is not None and not name.endswith(suffix):
                continue
            result.append(f)
        return result

    def list(self, path: str|Path, prefix: str|None = None, suffix: str|None = None, glob: bool|None = None) -> list[str]:
        full_path = self.folder / path
        if full_path.is_file():
            raise ValueError(f"{full_path} is a file")
        if not full_path.is_dir():
            return []
        return [str(f.relative_to(full_path)) for f in self._iter_files(full_path, prefix, suffix, glob)]

    def list_details(self, path: str|Path, prefix: str|None = None, suffix: str|None = None, glob: bool|None = None) -> list[FileDetails]:
        full_path = self.folder / path
        if full_path.is_file():
            raise ValueError(f"{full_path} is a file")
        if not full_path.is_dir():
            return []
        result = []
        for f in self._iter_files(full_path, prefix, suffix, glob):
            stat = f.stat()
            result.append(FileDetails(
                name=str(f.relative_to(full_path)),
                last_modification_date=datetime.fromtimestamp(stat.st_mtime),
            ))
        return result

    def open(self, filename: str|Path) -> Iterable[bytes]:
        full_path = self.folder / filename
        with full_path.open('rb') as f:
            while True:
                chunk = f.read(65536)
                if not chunk:
                    break
                yield chunk

    def upload(self, filename: str|Path, data: FileLike|Iterable[bytes]) -> None:
        full_path = self.folder / filename
        full_path.parent.mkdir(parents=True, exist_ok=True)
        FileLikeHandler.write(data, full_path)

    def delete(self, filename: str|Path) -> None:
        full_path = self.folder / filename
        if full_path.is_file():
            os.unlink(full_path)
        elif full_path.is_dir():
            shutil.rmtree(full_path)
        else:
            raise ValueError(f"Path {full_path} is not a file or a directory")

    def is_file(self, filename: str|Path) -> bool:
        return (self.folder / filename).is_file()

    def is_dir(self, filename: str|Path) -> bool:
        return (self.folder / filename).is_dir()


class StorageApi(IStorage):
    def __init__(self, base_url: str, custom_prefix: str|None = None) -> None:
        ApiCall.define_endpoints(self, base_url, IStorage, custom_prefix)