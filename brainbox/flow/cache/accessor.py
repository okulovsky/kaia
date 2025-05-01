from typing import Generic, TypeVar, Optional,Callable
from .cache_manager import ICacheManager
from abc import ABC, abstractmethod
import hashlib

TExternalKey = TypeVar('TExternalKey')
TInternalKey = TypeVar('TInternalKey')

class Accessor(Generic[TExternalKey, TInternalKey], ABC):
    def __init__(self, cache: ICacheManager[TInternalKey]):
        self.cache = cache

    def _hash_str(self, s: str):
        return hashlib.sha256(str(s).encode()).hexdigest()

    def _translate_external_key(self, key: TExternalKey) -> TInternalKey:
        return self._hash_str(str(key))

    @abstractmethod
    def _external_get(self, key: TExternalKey):
        pass

    def _postprocess(self, value):
        return value


    def get(self, key: TExternalKey):
        internal_key = self._translate_external_key(key)
        if not self.cache.contains(internal_key):
            value = self._external_get(key)
            self.cache.store(internal_key, value)
            if not self.cache.contains(internal_key):
                raise ValueError(f"Value for {key}/{internal_key} was not stored in cache")
        return self._postprocess(self.cache.unsafe_get(internal_key))







