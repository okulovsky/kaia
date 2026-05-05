import shutil
from enum import Enum
from pathlib import Path
from typing import Any
import pickle
import json

import pandas


class ResultType(Enum):
    Pickle = 0
    Json = 1
    Text = 2
    Parquet = 3

TYPE_TO_EXTENSION = {
    ResultType.Pickle: "",
    ResultType.Json: ".json",
    ResultType.Text: ".txt",
    ResultType.Parquet: ".parquet",
}

class FileResult:
    def __init__(self, path):
        self.path = path

def write_result(folder: Path, type: ResultType, data: Any):
    filename = folder/('result'+TYPE_TO_EXTENSION[type])

    if type == ResultType.Pickle:
        filename.write_bytes(pickle.dumps(data))
    elif type == ResultType.Json:
        filename.write_text(json.dumps(data))
    elif type == ResultType.Text:
        filename.write_text(data)
    elif type == ResultType.Parquet:
        data.to_parquet(filename)
    else:
        raise ValueError(f"Unknown result type: {type}")


def find_result(folder: Path) -> Path|None:
    for extension in TYPE_TO_EXTENSION.values():
        path = folder/('result'+extension)
        if path.is_file():
            return path

def read_result(path: Path) -> Any:
    type = next(type for type in ResultType if path.name=='result'+TYPE_TO_EXTENSION[type])
    if type == ResultType.Pickle:
        return pickle.loads(path.read_bytes())
    if type == ResultType.Json:
        return json.loads(path.read_text())
    if type == ResultType.Text:
        return path.read_text()
    if type == ResultType.Parquet:
        return pandas.read_parquet(path)
    else:
        raise ValueError(f"Unknown result type: {type}")


def remove_result(folder: Path):
    result_file = find_result(folder)
    if result_file is not None:
        result_file.unlink()

