import uuid
from collections.abc import Iterable
from io import BytesIO
from pathlib import Path
from typing import Any
from .file import File

FileLike = Path | str | bytes | BytesIO | File


class FileLikeHandler:
    @staticmethod
    def guess_name(filelike: FileLike, raise_if_no_name: bool = False):
        if isinstance(filelike, File):
            return filelike.name
        elif isinstance(filelike, str):
            return Path(filelike).name
        elif isinstance(filelike, Path):
            return filelike.name
        else:
            if raise_if_no_name:
                raise TypeError(f"FileLike {type(filelike)} does not have a name")
            return str(uuid.uuid4())

    @staticmethod
    def to_bytes_iterable(filelike, element_type: Any = None, chunk_size: int = 64 * 1024) -> Iterable[bytes]:
        # If str, Path -> Read the file, return bytes in chunks
        if isinstance(filelike, (str, Path)):
            with open(filelike, 'rb') as f:
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    yield chunk
            return
        # If bytes -> yield in chunks
        if isinstance(filelike, bytes):
            for i in range(0, len(filelike), chunk_size):
                yield filelike[i:i + chunk_size]
            return
        # If BytesIO -> yield in chunks
        if isinstance(filelike, BytesIO):
            filelike.seek(0)
            while True:
                chunk = filelike.read(chunk_size)
                if not chunk:
                    break
                yield chunk
            return
        if isinstance(filelike, File):
            for i in range(0, len(filelike.content), chunk_size):
                yield filelike.content[i:i + chunk_size]
            return
        # If iterable
        if isinstance(filelike, Iterable):
            for item in filelike:
                if isinstance(item, bytes):
                    # iterable[bytes] -> return it
                    yield item
                elif isinstance(item, str):
                    # iterable[str] -> encode as utf-8
                    yield item.encode('utf-8')
                else:
                    # iterable[Any] -> serialize with Reflector as json, encode utf-8
                    from ...reflector import SerializationContext
                    ctx = SerializationContext()
                    if element_type is not None:
                        import json
                        yield json.dumps(element_type.value_to_json(item, ctx)).encode('utf-8')
                    else:
                        import json
                        yield json.dumps(item).encode('utf-8')
            return
        raise ValueError(f"{type(filelike)} is not a supported FileLike type")

    @staticmethod
    def to_bytes(filelike) -> bytes:
        return b''.join(FileLikeHandler.to_bytes_iterable(filelike))

    @staticmethod
    def write(filelike, path: Path | str):
        with open(path, 'wb') as f:
            for chunk in FileLikeHandler.to_bytes_iterable(filelike):
                f.write(chunk)

