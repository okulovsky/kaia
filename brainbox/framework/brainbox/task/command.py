import os

from ..app import BrainBoxApi, IBrainBoxTask
from typing import TypeVar, Generic, Any
from pathlib import Path
from dataclasses import dataclass
from yo_fluq import FileIO

T = TypeVar("T")

@dataclass
class BrainBoxCommandCacheItem:
    id: str|None
    result: Any = None


class BrainBoxCommandCache(Generic[T]):
    def __init__(self, file: Path):
        self.file = file
        if file.name.endswith('.json'):
            self._as_json = True
        elif file.name.endswith('.pkl') or file.name.endswith('.pickle'):
            self._as_json = False
        else:
            raise ValueError(f"Filename for cache must end with .json or .pkl/.pickle, but was: {file.name}")

    def read(self) -> BrainBoxCommandCacheItem:
        if not self.file.parent.is_dir():
            return BrainBoxCommandCacheItem(None, None)
        if not self.file.is_file():
            return BrainBoxCommandCacheItem(None, None)
        if self._as_json:
            return BrainBoxCommandCacheItem(**FileIO.read_json(self.file))
        else:
            return FileIO.read_pickle(self.file)
    def get_cached_result(self) -> T|None:
        return self.read().result

    def update(self, id: str, result: T|None = None):
        os.makedirs(self.file.parent, exist_ok=True)
        if self._as_json:
            FileIO.write_json(dict(id=id, result=result), self.file)
        else:
            FileIO.write_pickle(BrainBoxCommandCacheItem(id, result))


class BrainBoxCommand(Generic[T]):
    Cache = BrainBoxCommandCache

    def __init__(self,
                 task: IBrainBoxTask,
                 cache: BrainBoxCommandCache|None = None
                 ):
        self.task = task
        self.cache = cache

    def with_cache(self, file: Path) -> 'BrainBoxCommand':
        return BrainBoxCommand(self.task, BrainBoxCommandCache(Path(file)))

    def execute(self, api: BrainBoxApi) -> T:
        if self.cache is not None:
            cached = self.cache.read()
            if cached.result is not None:
                return cached.result
            elif cached.id is not None:
                return self._join(api, cached.id)
        self.add(api)
        return self.join(api)


    def add(self, api: BrainBoxApi):
        if self.cache is not None:
            cached = self.cache.read()
            if cached.id is not None:
                return
        api.add(self.task)
        if self.cache is not None:
            self.cache.update(self.task.get_resulting_id())

    def _join(self, api: BrainBoxApi, id: str) -> T:
        result = api.join(id)
        result = self.task.postprocess_result(result, api)
        if self.cache is not None:
            self.cache.update(id, result)
        return result

    def join(self, api: BrainBoxApi) -> T:
        return self._join(api, self.task.get_resulting_id())

