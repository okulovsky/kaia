import os
from typing import *
from enum import Enum
from pathlib import Path
from yo_fluq import FileIO
from typing import TypeVar, Generic

TMetadata = TypeVar('TMetadata')

class File(Generic[TMetadata]):
    class Kind(Enum):
        Audio = 1
        Image = 2
        Json = 3
        Text = 4

    def __init__(self,
                 name: str,
                 content: None|bytes|str,
                 kind: Optional['File.Kind'] = None,
                 ):
        self.name = name
        if isinstance(content, str):
            self.content = content.encode('utf-8')
        else:
            self.content = content
        if kind is not None:
            self.kind = kind
        else:
            self.kind = File.guess_kind_from_filename(name)

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
        return File(filename.name, FileIO.read_bytes(filename), kind)

    def write(self, folder: Path|str):
        folder = Path(folder)
        os.makedirs(folder, exist_ok=True)
        path = folder/self.name
        FileIO.write_bytes(self.content, path)
        return path


    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f'File({self.name})'

    @property
    def metadata(self) -> TMetadata:
        if not hasattr(self, '_metadata'):
            raise ValueError("Metadata was not set for this file")
        return self._metadata

    @metadata.setter
    def metadata(self, value: TMetadata):
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




