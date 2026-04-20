from typing import TypeVar, Generic
from chara.common import ListCache, ICache
from pathlib import Path

TCase = TypeVar("TCase")
TCache = TypeVar("TCache", bound=ICache)

class UtilityCache(Generic[TCase, TCache], ICache[list[TCase]]):
    def __init__(self, t_cache: type[TCache], working_folder: Path|None = None):
        super().__init__(working_folder)
        self.buffer = ListCache[TCache, list[TCase]](t_cache)

