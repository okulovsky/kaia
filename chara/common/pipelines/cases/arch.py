import uuid
from typing import TypeVar, Generic, overload, Callable, TypeAlias
from ...cache import ICache
from abc import ABC, abstractmethod
from pathlib import Path

class ICase:
    @property
    def error(self) -> str|None:
        if not hasattr(self, '_error'):
            return None
        return self._error

    @error.setter
    def error(self, value: str|None) -> None:
        self._error = value


TCase = TypeVar('TCase', bound=ICase)
TCache = TypeVar('TCache')

class CaseCache(ICache[list[TCase]], Generic[TCase]):
    def __init__(self, working_folder: Path|None = None):
        super().__init__(working_folder)

    def read_cases(self) -> list[TCase]:
        return self.read_result()

    def read_successful_cases(self, raise_if_any_errors: bool = False) -> list[TCase]:
        result = []
        for case in self.read_result():
            if case.error:
                if raise_if_any_errors:
                    raise ValueError(f"Error found\n{case.error}")
            else:
                result.append(case)
        return result



    @overload
    def create_subcache(self, name: str) -> 'CaseCache[TCase]': ...

    @overload
    def create_subcache(self, name: str, factory: Callable[[TCache], None]) -> TCache: ...

    @overload
    def create_subcache(self, name: str, factory: type[TCache]) -> TCache: ...

    def create_subcache(self, name: str, factory: type[TCache]|None = None):
        if factory is None:
            factory = CaseCache
        inner_cache = factory()
        inner_cache.initialize(self.working_folder/name)
        return inner_cache

ICasePipeline: TypeAlias = Callable[[CaseCache[TCase], list[TCase]], None]

def safe_id():
    return str(uuid.uuid4()).replace('-','')