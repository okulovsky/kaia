from typing import *
from dataclasses import dataclass
from pathlib import Path
from enum import Enum
from pathlib import Path
from kaia.infra import FileIO



class File:
    class Kind(Enum):
        Audio = 1
        Image = 2
        Json = 3

    def __init__(self,
                 name: str,
                 content: None|bytes|str,
                 kind: Optional['File.Kind'] = None,
                 metadata: Optional[Dict[str,Any]] = None
                 ):
        self.name = name
        if isinstance(content, str):
            self.content = content.encode('utf-8')
        else:
            self.content = content
        self.kind = kind
        self.metadata = metadata

    @property
    def string_content(self):
        if self.content is None:
            return None
        return self.content.decode('utf-8')


    @staticmethod
    def _dump(file: 'File', cache_folder: Path):
        with open(cache_folder / file.name, 'wb') as stream:
            stream.write(file.content)
            file.content = None

    @staticmethod
    def brainbox_postprocess(obj, cache_folder: Path):
        if isinstance(obj, File):
            File._dump(obj, cache_folder)
        elif isinstance(obj, tuple) or isinstance(obj, list):
            for element in obj:
                if isinstance(element, File):
                    File._dump(element, cache_folder)

    @staticmethod
    def read(filename: str|Path):
        filename = Path(filename)
        extension = filename.name.split('.')[-1]
        kind = None
        for key, value in _FILETYPES.items():
            if extension in value:
                kind = key
        return File(filename.name, FileIO.read_bytes(filename), kind)

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f'File({self.name})'



_FILETYPES = {
    File.Kind.Audio: {'wav','mp3','ogg'},
    File.Kind.Image: {'png','jpg','jpeg','bmp'},
    File.Kind.Json: {'json'}
}




