import os
from dataclasses import dataclass
from typing import Optional
from enum import Enum
from pathlib import Path


@dataclass(repr=False, eq=False)
class File:
    class Kind(Enum):
        Audio = 1
        Image = 2
        Json = 3
        Text = 4

    name: str
    content: Optional[bytes]
    kind: Optional['File.Kind'] = None

    def __post_init__(self):
        if isinstance(self.content, str):
            self.content = self.content.encode('utf-8')
        if self.kind is None:
            self.kind = File.guess_kind_from_filename(self.name)

    @property
    def string_content(self):
        if self.content is None:
            return None
        return self.content.decode('utf-8')

    @staticmethod
    def guess_kind_from_filename(filename: str):
        extension = filename.split('.')[-1]
        kind = None
        for key, value in _FILETYPES.items():
            if extension in value:
                kind = key
        return kind

    @staticmethod
    def read(filename: str|Path):
        filename = Path(filename)
        kind = File.guess_kind_from_filename(filename.name)
        return File(filename.name, filename.read_bytes(), kind)

    def write(self, folder: Path|str):
        folder = Path(folder)
        os.makedirs(folder, exist_ok=True)
        path = folder/self.name
        with open(path, 'wb') as f:
            f.write(self.content)
        return path

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f'File({self.name})'

    @property
    def metadata(self):
        if not hasattr(self, '_metadata'):
            raise ValueError("Metadata was not set for this file")
        return self._metadata

    @metadata.setter
    def metadata(self, value):
        self._metadata = value

    def has_metadata(self, _type: type = None):
        if not hasattr(self, '_metadata'):
            return False
        if self._metadata is None:
            return False
        if _type is not None and not isinstance(self._metadata, _type):
            return False
        return True


_FILETYPES = {
    File.Kind.Audio: {'wav','mp3','ogg'},
    File.Kind.Image: {'png','jpg','jpeg','bmp'},
    File.Kind.Json: {'json'},
    File.Kind.Text: {'txt'}
}
