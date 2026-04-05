from .log_item import ILogItem
from .logger_class import Logger
from pathlib import Path

class HtmlReport:
    def __init__(self, file: Path):
        self._file = file

    def __enter__(self):
        self._file_handle = open(self._file, 'w')
        self._file_handle.write(
            "<!DOCTYPE html>"
            "<html>"
            "<head><meta charset='utf-8'></head>"
            "<body>"
        )
        self._file_handle.flush()
        Logger.ON_ITEM.append(self)
        return self

    def __call__(self, item: ILogItem ):
        self._file_handle.write(item.to_html() + '\n\n')
        self._file_handle.flush()

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self in Logger.ON_ITEM:
            Logger.ON_ITEM.remove(self)
        if self._file_handle is not None:
            self._file_handle.close()
            self._file_handle = None