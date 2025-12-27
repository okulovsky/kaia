import os
from .cache_entity import IFinalizableCacheEntity, TResult
from typing import Generic, Iterable, Callable, TypeVar, Tuple


TInnerCache = TypeVar('TInnerCache')

class DictCache(Generic[TInnerCache, TResult], IFinalizableCacheEntity[TResult]):
    def __init__(self,
                 cache_factory: Callable[[], TInnerCache],
                 ):
        self.cache_factory = cache_factory

    def read_subcaches(self) -> Iterable[Tuple[str, TInnerCache]]:
        for name in os.listdir(self.working_folder):
            if not (self.working_folder/name).is_dir():
                continue
            subcache = self._create_cache(name)
            if subcache.ready:
                yield name, subcache

    def read_subcache(self, name: str) -> TInnerCache|None:
        folder = self.working_folder/name
        if not folder.is_dir():
            return None
        return self._create_cache(name)

    def create_subcache(self, name: str) -> TInnerCache:
        return self._create_cache(name)

    def __getitem__(self, name: str) -> TInnerCache:
        return self.create_subcache(name)

    def _create_cache(self, name: str):
        cache = self.cache_factory()
        cache.initialize(self.working_folder/name)
        return cache
