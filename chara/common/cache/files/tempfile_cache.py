import os
import shutil
from ..core import ICacheEntity
from pathlib import Path
from typing import Iterable

class TempfileCache(ICacheEntity):
    @property
    def cache_file_path(self) -> Path:
        return self.working_folder/'cache'

    @property
    def ready(self) -> bool:
        return self.cache_file_path.is_file()

    @property
    def temp_file(self) -> Path:
        return self.working_folder / 'temp'

    def _update(self, line: str):
        os.makedirs(self.working_folder, exist_ok=True)
        if '\n' in line:
            raise ValueError("No newline is allowed")
        with open(self.temp_file, 'a') as f:
            f.write(line+'\n')

    def _read(self) -> Iterable[str]:
        if not self.ready:
            raise ValueError("Attempt to read the unfinished cache")
        with open(self.cache_file_path, 'r') as f:
            for line in f:
                yield line.strip()


    def finalize(self):
        os.makedirs(self.working_folder, exist_ok=True)
        if not self.temp_file.exists():
            with open(self.temp_file, 'w') as f:
                pass
        shutil.move(self.temp_file, self.cache_file_path)

