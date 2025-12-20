from typing import Generic, TypeVar, Iterable
from yo_fluq import Queryable, FileIO
from abc import abstractmethod, ABC
from pathlib import Path
import os
from contextlib import contextmanager
from .cache_entity import ICacheEntity

T = TypeVar('T')

class SegmentedCache(Generic[T], ICacheEntity):
    @property
    def counts_file(self) -> Path:
        return self.working_folder/'counts.json'

    @abstractmethod
    def _read_internal(self, count: int) -> Iterable[T]:
        ...

    @abstractmethod
    def _initialize_counts(self):
        ...

    @abstractmethod
    def _write_and_update_counts(self, item: T, counts: dict):
        ...

    def _end_writing_internal(self):
        pass

    def _start_writing_internal(self):
        pass


    @contextmanager
    def session(self):
        self._counts = self._initialize_counts()
        self._writing = True
        if self.counts_file.is_file():
            os.unlink(self.counts_file)
        self._start_writing_internal()
        try:
            yield
            FileIO.write_json(self._counts, self.counts_file)
        finally:
            self._end_writing_internal()
            self._writing = False


    def write(self, item: T):
        if not hasattr(self, '_writing') or not self._writing:
            raise ValueError("Writing is only possible in session")
        self._write_and_update_counts(item, self._counts)

    @property
    def ready(self) -> bool:
        return self.counts_file.exists()

    def read(self) -> Queryable[T]:
        counts = FileIO.read_json(self.counts_file)
        return Queryable(self._read_internal(counts['records']), counts['records'])



