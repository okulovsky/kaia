from typing import *
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass
class StorageRecord:
    id: int
    timestamp: datetime
    value: Any


class IStorage(ABC):
    @abstractmethod
    def save(self, key: str, value: Any):
        pass

    def load(self, key: Optional[str] = None, amount: Optional[int] = None, historical_order=True) -> List[Any]:
        records = self.load_update(key = key, amount = amount, historical_order=historical_order)
        return [v.value for v in records]

    @abstractmethod
    def load_update(self,
                   key: Optional[str] = None,
                   amount: Optional[int] = None,
                   last_update_id: Optional[int] = None,
                   last_update_timestamp: Optional[datetime] = None,
                   historical_order: bool = True
                   ) -> List[StorageRecord]:
        pass

