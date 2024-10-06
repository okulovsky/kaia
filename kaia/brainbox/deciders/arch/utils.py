from typing import Any
from unittest import TestCase
from kaia.infra import Loc
from pathlib import Path
from io import BytesIO
from ...core import File
from kaia.infra import FileIO
from dataclasses import dataclass


def check_if_its_sound(file, tc: TestCase):
    import soundfile as sf
    with Loc.create_temp_file('sound_files_to_check', 'wb') as tmp_filename:
        FileIO.write_bytes(file.content, tmp_filename)
        f = sf.SoundFile(tmp_filename)
        duration = f.frames / f.samplerate
        tc.assertGreater(duration, 1)
    f.close()

class FileLike:
    Type = str|Path|bytes|File|BytesIO

    @dataclass
    class AlreadyStream:
        stream: Any


    def __init__(self, file: str|Path|bytes|BytesIO, cache_folder: None|Path):
        self.file = file
        self.cache_folder = cache_folder
        self.stream = None

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