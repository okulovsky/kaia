from abc import ABC, abstractmethod
from datetime import datetime
from dataclasses import dataclass

@dataclass
class SerializableLogItem:
    timestamp: datetime
    line: str
    html: str
    is_error: bool

class ILogItem(ABC):
    @abstractmethod
    def to_string(self) -> str:
        pass

    def to_html(self) -> str:
        return self.to_string()

    @property
    def timestamp(self) -> datetime|None:
        if not hasattr(self, '_timestamp'):
            return None
        return self._timestamp

    @timestamp.setter
    def timestamp(self, timestamp: datetime) -> None:
        self._timestamp = timestamp

    def to_serializable(self) -> SerializableLogItem:
        from .simple import ExceptionItem
        return SerializableLogItem(
            self.timestamp if self.timestamp else datetime.now(),
            self.to_string(),
            self.to_html(),
            isinstance(self, ExceptionItem)
        )


