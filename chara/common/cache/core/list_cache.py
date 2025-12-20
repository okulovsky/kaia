from .cache_entity import IFinalizableCacheEntity, TResult
from typing import Generic, Iterable, Callable, TypeVar
from pathlib import Path


TInnerCache = TypeVar('TInnerCache')

class ListCache(Generic[TInnerCache, TResult], IFinalizableCacheEntity[TResult]):
    def __init__(self,
                 cache_factory: Callable[[], TInnerCache],
                 right_zeroes: int = 4
                 ):
        self.cache_factory = cache_factory
        self.right_zeroes = right_zeroes

    def read_subcaches(self) -> Iterable[TInnerCache]:
        index = 0
        while True:
            folder = self._subcache_folder(index)
            if not folder.is_dir():
                break
            subcache = self._create_cache(folder)
            if subcache.ready:
                yield subcache
            else:
                break
            index+=1

    def read_subcache(self, index: int) -> TInnerCache|None:
        folder = self._subcache_folder(index)
        if not folder.is_dir():
            return None
        return self._create_cache(folder)

    def create_subcache(self, index: int) -> TInnerCache:
        return self._create_cache(self._subcache_folder(index))

    def _subcache_folder(self, index: int) -> Path:
        folder = self.working_folder / str(index).zfill(self.right_zeroes)
        return folder

    def _create_cache(self, folder):
        cache = self.cache_factory()
        cache.initialize(folder)
        return cache
