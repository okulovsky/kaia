import json
import pickle
from pathlib import Path
from foundation_kaia.marshalling import Serializer
from typing import Any
import pandas as pd
from .result_type import ResultType
import dataclasses

class PickleType(ResultType):
    def get_extension(self) -> str:
        return ".pickle"

    def accepts_data(self, data) -> bool:
        return True

    def write(self, data, path: Path):
        path.write_bytes(pickle.dumps(data))

    def read(self, path: Path):
        return pickle.loads(path.read_bytes())

class TextType(ResultType):
    def get_extension(self) -> str:
        return ".txt"

    def accepts_data(self, data) -> bool:
        return isinstance(data, str)

    def write(self, data, path: Path):
        path.write_text(data, 'utf-8')

    def read(self, path: Path):
        return path.read_text()

class JsonType(ResultType):
    def get_extension(self) -> str:
        return ".json"

    @staticmethod
    def is_json_compatible(data) -> bool:
        if isinstance(data, (str, int, bool)):
            return True
        if dataclasses.is_dataclass(data) and not isinstance(data, type):
            return True
        if isinstance(data, list):
            return all(JsonType.is_json_compatible(item) for item in data)
        if isinstance(data, dict):
            return all(isinstance(k, str) and JsonType.is_json_compatible(v) for k, v in data.items())
        return False

    def accepts_data(self, data) -> bool:
        return JsonType.is_json_compatible(data)


    def write(self, data, path: Path):
        path.write_text(json.dumps(Serializer.parse(Any).to_json(data), indent=4))

    def read(self, path: Path):
        return Serializer.parse(Any).from_json(json.loads(path.read_text()))

class PathType(ResultType):
    def get_extension(self) -> str:
        return ".path.txt"

    def accepts_data(self, data) -> bool:
        return isinstance(data, Path)

    def write(self, data, path: Path):
        path.write_text(str(data))

    def read(self, path: Path):
        return Path(path.read_text())


class ParquetType(ResultType):
    def get_extension(self) -> str:
        return ".parquet"

    def accepts_data(self, data) -> bool:
        return isinstance(data, pd.DataFrame)

    def write(self, data, path: Path):
        data.to_parquet(str(path))

    def read(self, path: Path):
        return pd.read_parquet(str(path))