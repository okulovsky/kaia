import json
import os

from ..core import SegmentedCache
from typing import Generic, TypeVar, Iterable
from pathlib import Path


T = TypeVar('T')

class JsonlCache(Generic[T], SegmentedCache[T]):
    def __init__(self):
        super().__init__()
        self.stream = None

    @property
    def cache_file_path(self) -> Path:
        return self.working_folder/'cache'

    def _initialize_counts(self):
        return dict(records=0)

    def _start_writing_internal(self):
        os.makedirs(self.working_folder, exist_ok=True)
        self.stream = open(self.cache_file_path, 'w')

    def _write_and_update_counts(self, item: T, counts: dict):
        self.stream.write(json.dumps(item, ensure_ascii=False) + '\n')
        counts['records'] += 1

    def _end_writing_internal(self):
        if self.stream is not None:
            self.stream.close()

    def _read_internal(self, count: int) -> Iterable[T]:
        with open(self.cache_file_path, 'r') as f:
            for line in f:
                yield json.loads(line)







