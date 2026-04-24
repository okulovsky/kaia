from abc import ABC, abstractmethod
from typing import Iterable
from foundation_kaia.marshalling import endpoint, service

@service
class IStreamingStorage:
    @endpoint
    def read(self, filename: str) -> Iterable[bytes]:
        """Streams the contents of a stored file as byte chunks."""
        ...

    @endpoint
    def write(self, filename: str, data: Iterable[bytes]) -> None:
        """Writes a byte stream to a file in one operation."""
        ...

    @endpoint
    def begin_writing(self, filename: str) -> None:
        """Initializes a file slot for incremental chunk writing."""
        ...

    @endpoint
    def append(self, filename: str, data: bytes, chunk_index: int|None = None) -> None:
        """Appends a byte chunk to a file being written incrementally."""
        ...

    @endpoint
    def commit(self, filename: str) -> None:
        """Finalizes an incrementally written file, making it readable."""
        ...

    @endpoint
    def delete(self, filename: str) -> None:
        """Removes a stored file."""
        ...