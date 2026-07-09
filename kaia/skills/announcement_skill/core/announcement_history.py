from dataclasses import dataclass
from datetime import datetime
from abc import ABC, abstractmethod
from foundation_kaia.marshalling import Serializer
import json
from pathlib import Path

@dataclass
class AnnouncementRecord:
    announcement_name: str
    timestamp: datetime
    feedback: str|None
    username: str

class IAnnouncementHistory(ABC):
    @abstractmethod
    def get_records(self) -> list[AnnouncementRecord]:
        pass

    @abstractmethod
    def add_record(self, record: AnnouncementRecord):
        pass


class FileAnnouncementHistory(IAnnouncementHistory):
    def __init__(self, filename: Path|None = None):
        self.filename = filename
        self.serializer = Serializer.parse(AnnouncementRecord)
        self.records: list[AnnouncementRecord] = []
        self.loaded_amount_per_announcement = 10
        if self.filename is not None:
            self._read()

    def _read(self):
        name_to_records = {}
        if self.filename.exists():
            with open(self.filename) as f:
                for line in f:
                    record = self.serializer.from_json(json.loads(line))
                    if record.announcement_name not in name_to_records:
                        name_to_records[record.announcement_name] = []
                    ar = name_to_records[record.announcement_name]
                    ar.append(record)
                    if len(ar) > 10:
                        ar = ar[-10:]
                    name_to_records[record.announcement_name] = ar
        all_records = []
        for v in name_to_records.values():
            all_records.extend(v)
        self.records = list(sorted(all_records, key=lambda x: x.timestamp))


    def get_records(self) -> list[AnnouncementRecord]:
        return list(self.records)


    def add_record(self, record: AnnouncementRecord):
        if self.filename is not None:
            with open(self.filename, 'a') as f:
                f.write(json.dumps(self.serializer.to_json(record))+"\n")
        self.records.append(record)

