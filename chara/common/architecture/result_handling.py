from pathlib import Path
from typing import Any
from .file_handling import FolderHandler

def write_result(folder: Path, data: Any):
    FolderHandler(folder).write('result', data)

def find_result(folder: Path) -> Path|None:
    return FolderHandler(folder).get_file('result')

def read_result(folder: Path) -> Any:
    return FolderHandler(folder).read('result')

def remove_result(folder: Path):
    result_file = find_result(folder)
    if result_file is not None:
        result_file.unlink()

