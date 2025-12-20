import os
import uuid

from ..core import IFinalizableCacheEntity
from brainbox import File
from pathlib import Path
from yo_fluq import FileIO
from typing import Iterable, TypeVar, Generic
from yo_fluq import Queryable

TMetadata = TypeVar('TMetadata')

class FolderCache(Generic[TMetadata], IFinalizableCacheEntity[None]):
    def __init__(self):
        super().__init__()

    def get_metadata_path(self, name: str) -> Path:
        return self.working_folder/(name+'.metadata')

    def write(self,  item: File|bytes|Path|str):
        if isinstance(item, bytes):
            name = str(uuid.uuid4())
            metadata = None
            bts = item
        elif isinstance(item, File):
            name = item.name
            if item.has_metadata():
                metadata = item.metadata
            else:
                metadata = None
            bts = item.content
        elif isinstance(item, str) or isinstance(item, Path):
            name = Path(item).name
            bts = FileIO.read_bytes(item)
            metadata = None
        else:
            raise ValueError(f"item expected to be bytes, File, path or str with path, but was {type(item)}")
        os.makedirs(self.working_folder, exist_ok=True)
        FileIO.write_bytes(bts, self.working_folder/name)
        if metadata is not None:
            FileIO.write_pickle(metadata, self.get_metadata_path(name))


    def read_file(self, name: str) -> File:
        bts = FileIO.read_bytes(self.working_folder / name)
        file = File(name, bts)
        if self.get_metadata_path(name).exists():
            file.metadata = FileIO.read_pickle(self.get_metadata_path(name))
        return file

    def read_paths(self) -> list[Path]:
        result = []
        for c in os.listdir(self.working_folder):
            if c==self.result_file.name:
                continue
            if c.endswith('.metadata'):
                continue
            if c == self.log_path.name:
                continue
            result.append(self.working_folder/c)
        return result

    def read_files(self) -> Queryable[File]:
        paths = self.read_paths()
        return Queryable(paths).select(lambda z: self.read_file(z.name))

