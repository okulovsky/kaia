import os
from pathlib import Path

from ..core import SegmentedCache
from typing import Generic, Iterable, TypeVar
from yo_fluq import FileIO

T = TypeVar('T')

class MultifileCache(Generic[T], SegmentedCache[T]):
    def _get_filename(self, index):
        return self.working_folder/(str(index).zfill(6)+".pkl")

    def _initialize_counts(self):
        return dict(records=0)

    def _write_and_update_counts(self, item: T, counts):
        FileIO.write_pickle(item, self._get_filename(counts['records']))
        counts['records'] += 1

    def _read_internal(self, count: int) -> Iterable[T]:
        for i in range(count):
            yield FileIO.read_pickle(self._get_filename(i))

    def _start_writing_internal(self):
        os.makedirs(self.working_folder, exist_ok=True)

