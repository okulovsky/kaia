from typing import *
from pathlib import Path
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


class DictDataProvider(IDataProvider):
    def __init__(self, records: list[dict], filename_key: str):
        self.records = records
        self.filename_key = filename_key

    def get_records(self) -> list[IDataProvider.Record]:
        return [
            IDataProvider.Record(
                r[self.filename_key],
                {k: v for k, v in r.items() if k != self.filename_key and v is not None},
                r,
            )
            for r in self.records
        ]


