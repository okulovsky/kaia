import json
import os
import zipfile
import threading
from datetime import date
from pathlib import Path


def _zip_and_delete(jsonlines_path: Path):
    zip_path = jsonlines_path.with_suffix('.zip')
    with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(jsonlines_path, jsonlines_path.name)
    jsonlines_path.unlink()


class Stasher:
    def __init__(self, folder: Path):
        self.folder = Path(folder)
        self.current_date: date | None = None
        self.current_file: Path | None = None
        self._fh = None

    def stash(self, record: dict):
        today = date.today()
        if self.current_date is None or self.current_date < today:
            os.makedirs(self.folder, exist_ok=True)
            if self._fh is not None:
                self._fh.close()
                threading.Thread(target=_zip_and_delete, args=(self.current_file,), daemon=True).start()
            self.current_date = today
            self.current_file = self.folder / f"log_{today:%Y_%m_%d}.jsonlines"
            self._fh = open(self.current_file, 'a')

        self._fh.write(json.dumps(record) + '\n')
        self._fh.flush()

