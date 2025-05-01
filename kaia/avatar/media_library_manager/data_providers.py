from typing import *
from pathlib import Path
from brainbox import MediaLibrary
from abc import ABC, abstractmethod
from dataclasses import dataclass

TRecord = TypeVar('TRecord')


class IDataProvider(ABC):
    @dataclass
    class Record:
        filename: str
        tags: dict
        original_record: Any

    @abstractmethod
    def get_records(self) -> list['IDataProvider.Record']:
        pass



class MediaLibraryDataProvider(IDataProvider):
    def __init__(self, media_library: Path|str|MediaLibrary):
        if isinstance(media_library, MediaLibrary):
            self.media_library = media_library
        else:
            self.media_library = MediaLibrary.read(media_library)

    def get_records(self) -> list[MediaLibrary.Record]:
        return [IDataProvider.Record(r.filename, r.tags, r) for r in self.media_library.records]

class DataClassDataProvider(IDataProvider, Generic[TRecord]):
    def __init__(self, records: list[TRecord], filename_field: str = 'filename'):
        self.records = records
        self.filename_field = filename_field

    def get_records(self) -> list[TRecord]:
        return [IDataProvider.Record(
            getattr(r, self.filename_field),
            {k:v for k,v in r.__dict__.items() if k!=self.filename_field},
            r
        ) for r in self.records]
