import os
from typing import Iterable
from pathlib import Path
import json
from .streaming_storage_interface import IStreamingStorage
from .streaming_reader import StreamingFolderStorageReader

class StreamingStorage(IStreamingStorage):
    def __init__(self, folder: Path):
        self.folder = folder
        self.buffer: dict[str, dict[int, bytes]] = {}
        self.current_chunks: dict[str, int] = {}

    def _check_filename(self, filename: str):
        if '/' in filename:
            raise ValueError(f"Filename must not contain '/': {filename!r}")

    def _get_path(self, filename: str) -> Path:
        self._check_filename(filename)
        return self.folder / filename

    def _get_tempfile_path(self, filename: str) -> Path:
        self._check_filename(filename)
        return self.folder / (filename+".streaming_tempfile")

    def read(self, filename: str, timeout: float = 60) -> Iterable[bytes]:
        return StreamingFolderStorageReader(self._get_path(filename), self._get_tempfile_path(filename), timeout)

    def begin_writing(self, filename: str) -> None:
        self.current_chunks[filename] = 0
        self.buffer[filename] = {}
        path = self._get_path(filename)
        if path.is_file():
            os.unlink(path)
        tmp = self._get_tempfile_path(filename)
        with open(tmp, "w") as f:
            f.write(json.dumps(dict(event="started"))+"\n")
        with open(path, 'wb') as f:
            pass

    def _buffer_data(self, filename: str, data: bytes, chunk_index: int|None = None) -> list[bytes]:
        if chunk_index is None:
            self.current_chunks[filename] += 1
            data_items = [data]
        else:
            if chunk_index > self.current_chunks[filename]:
                self.buffer[filename][chunk_index] = data
                data_items = []
            else:
                data_items = [data]
                while True:
                    self.current_chunks[filename] += 1
                    idx = self.current_chunks[filename]
                    if idx in self.buffer[filename]:
                        data_items.append(self.buffer[filename][idx])
                        del self.buffer[filename][idx]
                    else:
                        break
        return data_items

    def append(self, filename: str, data: bytes, chunk_index: int|None = None) -> None:
        data_items = self._buffer_data(filename, data, chunk_index)
        with open(self._get_path(filename), "ab") as f_file:
            with open(self._get_tempfile_path(filename), 'a') as f_tmp:
                for item in data_items:
                    f_file.write(item)
                    f_tmp.write(json.dumps(dict(event='appended', size=len(item)))+"\n")

    def commit(self, filename: str) -> None:
        tmp = self._get_tempfile_path(filename)
        if not tmp.is_file():
            raise ValueError("Already committed")
        os.unlink(tmp)
        del self.current_chunks[filename]
        del self.buffer[filename]

    def delete(self, filename: str) -> None:
        if filename in self.current_chunks:
            del self.current_chunks[filename]
        if filename in self.buffer:
            del self.buffer[filename]
        path = self._get_path(filename)
        if not path.is_file():
            raise ValueError("File not found")
        os.unlink(path)
        tmp = self._get_tempfile_path(filename)
        if tmp.is_file():
            os.unlink(tmp)








