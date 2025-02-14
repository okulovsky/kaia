from typing import *
from .file import File
from pathlib import Path
from io import BytesIO
from dataclasses import dataclass
from uuid import uuid4


class FileLike:
    Type = str|Path|bytes|File|BytesIO

    @dataclass
    class AlreadyStream:
        stream: Any


    def __init__(self, file: str|Path|bytes|BytesIO, cache_folder: None|Path):
        self.file = file
        self.cache_folder = cache_folder
        self.stream = None

    @staticmethod
    def get_name(file: 'FileLike.Type', raise_if_no_name: bool = False):
        if isinstance(file, str):
            return file
        elif isinstance(file, Path):
            return file.name
        elif isinstance(file, File):
            return file.name
        else:
            if raise_if_no_name:
                raise ValueError("This FileLike must define a name, but doesn't")
            return str(uuid4())

    @staticmethod
    def get_name_and_extension(file: 'FileLike.Type'):
        parts = FileLike.get_name(file).split('.')
        if len(parts) == 1:
            return parts[0], ''
        return '.'.join(parts[:-1]), '.'+parts[-1]

    def get_path(self, extension_if_caching: str|None = None):
        if isinstance(self.file, Path):
            return self.file
        elif isinstance(self.file, str):
            if self.cache_folder is None:
                return self.file
            else:
                return self.cache_folder/self.file
        else:
            name = str(uuid4())
            if extension_if_caching is not None:
                name += '.' + extension_if_caching
            path = self.cache_folder/name
            with self as stream:
                data = stream.read()
                with open(path,'wb') as out_stream:
                    out_stream.write(data)
            return path

    def __enter__(self):
        if isinstance(self.file, Path):
            self.stream = open(self.file, 'rb')
        elif isinstance(self.file, str):
            if self.cache_folder is None:
                self.stream = open(self.file, 'rb')
            else:
                self.stream = open(self.cache_folder/self.file, 'rb')
        elif isinstance(self.file, bytes):
            self.stream = BytesIO(self.file)
        elif isinstance(self.file, File):
            if self.file.content is not None:
                self.stream = BytesIO(self.file.content)
            elif self.cache_folder is not None:
                self.stream = open(self.cache_folder / self.file.name, 'rb')
            else:
                self.stream = open(self.file.name, 'rb')
        elif isinstance(self.file, FileLike.AlreadyStream):
            self.stream = self.file.stream
        else:
            raise ValueError(f'File should be path, str (with path) or bytes, but was: {self.file}')
        return self.stream

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stream.close()