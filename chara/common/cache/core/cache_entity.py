import os
import shutil
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Self, Generic, TypeVar
from yo_fluq import FileIO

TResult = TypeVar('TResult')


class ICacheEntity(ABC):
    def initialize(self, working_folder: Path) -> Self:
        self._cache_entity_working_folder = working_folder
        return self

    @property
    def working_folder(self) -> Path:
        if not hasattr(self, '_cache_entity_working_folder'):
            raise ValueError("Cache was not properly initialized")
        return self._cache_entity_working_folder

    @property
    def name(self) -> str:
        return self.working_folder.name

    @property
    def log_path(self) -> Path:
        return self.working_folder / 'log'

    @property
    @abstractmethod
    def ready(self) -> bool:
        pass


    def delete(self) -> None:
        shutil.rmtree(self.working_folder, ignore_errors=True)


class IFinalizableCacheEntity(Generic[TResult], ICacheEntity):
    @property
    def result_file(self) -> Path:
        return self.working_folder / 'result'

    def write_result(self, result: TResult|None = None) -> None:
        os.makedirs(self.result_file.parent, exist_ok=True)
        FileIO.write_pickle(result, self.result_file)

    def finalize(self):
        self.write_result(None)

    def read_result(self) -> TResult:
        return FileIO.read_pickle(self.result_file)

    @property
    def ready(self) -> bool:
        return self.result_file.is_file()






