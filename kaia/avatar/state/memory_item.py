from datetime import datetime

class MemoryItem:
    @property
    def timestamp(self) -> datetime:
        if not hasattr(self, '_timestamp'):
            raise ValueError("timestamp was not set")
        return self._timestamp

    @timestamp.setter
    def timestamp(self, value: datetime):
        self._timestamp = value


