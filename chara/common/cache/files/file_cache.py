import os
from enum import Enum
from pathlib import Path
from typing import TypeVar, Generic
from yo_fluq import FileIO
from ..core import ICacheEntity

class FileCacheType(Enum):
    Pickle = 0
    Json = 1
    Text = 2
    Bytes = 3

T = TypeVar('T')

class FileCache(Generic[T], ICacheEntity):
    Type = FileCacheType

    def __init__(self, file_type: FileCacheType = FileCacheType.Pickle):
        self.file_type = file_type

    @property
    def cache_file_path(self) -> Path:
        return self.working_folder/'cache'

    @property
    def ready(self) -> bool:
        return self.cache_file_path.is_file()


    def read(self) -> T:
        if self.file_type == FileCacheType.Pickle:
            return FileIO.read_pickle(self.cache_file_path)
        elif self.file_type == FileCacheType.Json:
            return FileIO.read_json(self.cache_file_path)
        elif self.file_type == FileCacheType.Text:
            return FileIO.read_text(self.cache_file_path)
        elif self.file_type == FileCacheType.Bytes:
            return FileIO.read_bytes(self.cache_file_path)
        else:
            raise ValueError(f"Unsupported file type {self.file_type}")

    def write(self, data: T):
        os.makedirs(self.working_folder, exist_ok=True)
        if self.file_type == FileCacheType.Pickle:
            FileIO.write_pickle(data, self.cache_file_path)
        elif self.file_type == FileCacheType.Json:
            FileIO.write_json(data, self.cache_file_path)
        elif self.file_type == FileCacheType.Text:
            FileIO.write_text(data, self.cache_file_path)
        elif self.file_type == FileCacheType.Bytes:
            if not isinstance(data, bytes) and not isinstance(data, bytearray):
                raise ValueError(f"Data must be bytes or bytearray, but was {type(data)}")
            FileIO.write_bytes(data, self.cache_file_path)
        else:
            raise ValueError(f"Unsupported file type {self.file_type}")
