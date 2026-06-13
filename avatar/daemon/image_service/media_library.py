from dataclasses import dataclass
from pathlib import Path
from typing import Any
import zipfile
import json
from foundation_kaia.marshalling import Serializer
from foundation_kaia.marshalling.protocol.model.file_like import FileLike, FileLikeHandler


@dataclass
class Record:
    path: str
    tags: dict[str, Any]
    zip_path: Path|None = None

    def get_content(self) -> bytes:
        with zipfile.ZipFile(self.zip_path, 'r') as zp:
            return zp.read(self.path)

class MediaLibrary:
    Record = Record
    _serializer = None

    def __init__(self, *paths: Path):
        self.paths = paths
        self.records: list[Record] = []
        self._load()

    def _load(self):
        if MediaLibrary._serializer is None:
            MediaLibrary._serializer = Serializer.parse(list[Record])
        for path in self.paths:
            with zipfile.ZipFile(path, 'r') as zp:
                data = json.loads(zp.read('records.json'))
                records = MediaLibrary._serializer.from_json(data)
                for record in records:
                    record.zip_path = path
                self.records.extend(records)

    @classmethod
    def save(cls, path: Path, records: list['Record'], files: list[FileLike]) -> None:
        if cls._serializer is None:
            cls._serializer = Serializer.parse(list[Record])
        with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as zp:
            for file in files:
                zp.writestr(FileLikeHandler.guess_name(file), FileLikeHandler.to_bytes(file))
            zp.writestr('records.json', json.dumps(cls._serializer.to_json(records)))



