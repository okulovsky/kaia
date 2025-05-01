from .cache_manager import ICacheManager
from abc import ABC
from pathlib import Path
import os
from yo_fluq import *

class FileCacheManager(ICacheManager[str], ABC):
    def __init__(self, folder: Path, extension: str):
        self.folder = folder
        os.makedirs(self.folder, exist_ok=True)
        self.extension = extension

    def get_filename(self, key: str) -> Path:
        return self.folder/(key+'.'+self.extension)

    def contains(self, key: str) -> bool:
        return self.get_filename(key).is_file()

    def unsafe_delete(self, key: str):
        os.unlink(self.get_filename(key))


class JsonCacheManager(FileCacheManager):
    def __init__(self, folder: Path):
        super().__init__(folder, 'json')

    def unsafe_get(self, key: str):
        return FileIO.read_json(self.get_filename(key))

    def store(self, key: str, value):
        FileIO.write_json(value, self.get_filename(key))

