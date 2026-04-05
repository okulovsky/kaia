from abc import ABC, abstractmethod
from typing import Iterable
from foundation_kaia.marshalling_2 import endpoint, service

@service
class IStreamingStorage:
    @endpoint
    def read(self, filename: str) -> Iterable[bytes]:
        ...

    @endpoint
    def write(self, filename: str, data: Iterable[bytes]) -> None:
        ...

    @endpoint
    def begin_writing(self, filename: str) -> None:
        ...

    @endpoint
    def append(self, filename: str, data: bytes, chunk_index: int|None = None) -> None:
        ...

    @endpoint
    def commit(self, filename: str) -> None:
        ...

    @endpoint
    def delete(self, filename: str) -> None:
        ...