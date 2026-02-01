from .message_record import MessageRecord
from abc import ABC, abstractmethod


class LastMessageNotFoundException(ValueError):
    def __init__(self, last_message_id):
        super(LastMessageNotFoundException, self).__init__()
        self.last_message_id = last_message_id



class IMessageStore(ABC):
    @abstractmethod
    def add(self, msg: MessageRecord) -> None:
        pass

    @abstractmethod
    def last_id(self, session: str|None) -> str|None:
        pass

    @abstractmethod
    def tail(self,
             session: str | None,
             count: int | None,
             types: list[str] | None,
             except_types: list[str] | None
             ) -> list[MessageRecord]:
        pass

    @abstractmethod
    def get(self,
            session: str | None,
            count: int | None,
            last_message_id: str | None,
            types: list[str] | None,
            except_types: list[str] | None
            ) -> list[MessageRecord]:
        pass

