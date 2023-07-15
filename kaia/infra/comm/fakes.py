from typing import *
from .i_storage import IStorage, StorageRecord
from .i_messenger import IMessenger, MessengerQuery, Message
from datetime import datetime


class FakeStorage(IStorage):
    def save(self, key: str, value: Any):
        pass

    def load_update(self,
                   key: Optional[str] = None,
                   amount: Optional[int] = None,
                   last_update_id: Optional[int] = None,
                   last_update_timestamp: Optional[datetime] = None,
                   historical_order: bool = True
                   ) -> List[StorageRecord]:
        return []


class FakeMessenger(IMessenger):
    def add(self, payload: Any, *tags: str) -> str:
        pass

    def read(self, query: Optional[MessengerQuery] = None) -> List[Message]:
        return []

    def close(self, id: str, payload: Any):
        pass

