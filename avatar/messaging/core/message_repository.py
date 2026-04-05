from foundation_kaia.marshalling_2 import service, endpoint
from .message import IMessage
from .message_set import AvatarMessageSet
from abc import ABC, abstractmethod

@service
class IMessageRepository(ABC):
    @abstractmethod
    def put(self, session: str, message: IMessage):
        ...

    @abstractmethod
    def get(self,
            session: str,
            last_id: str | None = None,
            timeout_in_seconds: float | None = None,
            max_messages: int | None = None,
            allowed_types: list[str] | None = None,
            ) -> AvatarMessageSet[IMessage]:
        pass

    @abstractmethod
    def tail(self,
             session: str,
             count: int|None = None,
             from_timestamp=None,
             ) -> AvatarMessageSet[IMessage]:
        pass

    @abstractmethod
    def wait_for_availability(self):
        pass
