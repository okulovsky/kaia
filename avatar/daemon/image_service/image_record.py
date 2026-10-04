import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from ..common.content import IRecord


def _read_from_zip(zip_path: Path|None, file_id: str) -> bytes:
    if zip_path is None:
        raise ValueError(f"Cannot read the content of {file_id}: the records were loaded without an access to the media libraries")
    with zipfile.ZipFile(zip_path, 'r') as zp:
        return zp.read(file_id)


@dataclass
class VariantRecord(IRecord):
    file_id: str
    variant_type: str
    zip_path: Path|None = None

    def get_id(self) -> str:
        return self.file_id

    def get_tags(self) -> dict[str, Any]:
        return {'variant_type': self.variant_type}

    def get_content(self) -> bytes:
        return _read_from_zip(self.zip_path, self.file_id)


@dataclass
class ImageRecord(IRecord):
    file_id: str
    tags: dict[str, Any] = field(default_factory=dict)
    description: dict[str, Any] = field(default_factory=dict)
    zip_path: Path|None = None
    variants: list[VariantRecord] = field(default_factory=list)

    def get_id(self) -> str:
        return self.file_id

    def get_tags(self) -> dict[str, Any]:
        return self.tags

    def get_content(self) -> bytes:
        return _read_from_zip(self.zip_path, self.file_id)
