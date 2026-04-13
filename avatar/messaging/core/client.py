from .message_set import AvatarMessageSet
from .message import IMessage
from foundation_kaia.marshalling import JSON, TypeTools
from dataclasses import dataclass
import time
from yo_fluq import Query, Queryable
from typing import Type, TypeVar
from .message_repository import IMessageRepository
from loguru import logger

T = TypeVar('T')

@dataclass
class GenericMessage(IMessage):
    content_type: str
    content: JSON


class AvatarClient:
    def __init__(self,
                 repo: IMessageRepository,
                 session: str,
                 allowed_types: list[str] | None = None,
                 last_id: str|None = None
                 ):
        self.repo = repo
        self.session = session
        self.allowed_types = allowed_types
        self.last_id = last_id

    def base_pull(self, *, timeout_in_seconds: float|None = None, max_messages: int|None = None) -> AvatarMessageSet[IMessage]:
        result = self.repo.get(self.session, self.last_id, timeout_in_seconds, max_messages, self.allowed_types)
        if len(result.messages) > 0:
            self.last_id = result.messages[-1].envelop.id
        return result

    def push(self, message: IMessage):
        self.repo.put(self.session, message)

    def base_tail(self, count: int|None = None, *, from_timestamp=None) -> AvatarMessageSet[IMessage]:
        return self.repo.tail(self.session, count, from_timestamp=from_timestamp)

    def set_last_id(self, last_id: str|None = None):
        self.last_id = last_id

    def wait_for_availability(self):
        self.repo.wait_for_availability()

    def set_allowed_types(self, *allowed_types: type):
        if len(allowed_types) > 0:
            prefixes = []
            for t in allowed_types:
                if isinstance(t, type):
                    prefixes.append(TypeTools.type_to_full_name(t))
                else:
                    raise ValueError(f"Expected type, but was {t}")
            self.allowed_types = tuple(prefixes)
        else:
            self.allowed_types = None

    def clone_client(self) -> 'AvatarClient':
        return AvatarClient(self.repo, self.session, self.allowed_types, self.last_id)

    def pull(self, *, timeout_in_seconds: float|None = None, max_messages: int|None = None) -> list[IMessage]:
        return self.base_pull(timeout_in_seconds=timeout_in_seconds, max_messages=max_messages).messages

    def tail(self, count: int|None = None, *, from_timestamp=None) -> list[IMessage]:
        return self.base_tail(count, from_timestamp=from_timestamp).messages

    def _query(self, time_limit_in_seconds: float|None = None, no_exception: bool = False):
        begin = time.monotonic()
        collected_so_far = []
        while True:
            result = self.pull(max_messages=1, timeout_in_seconds=0.1)
            collected_so_far.extend(result)
            yield from result
            if time_limit_in_seconds is not None and (time.monotonic() - begin) > time_limit_in_seconds:
                if no_exception:
                    return
                else:
                    if len(collected_so_far) == 0:
                        report = "NO MESSAGES RECEIVED"
                    else:
                        try:
                            from ...messaging import ThreadCollection
                            report = ThreadCollection.just_print(collected_so_far, True)
                        except:
                            report = 'Errors when generating the report'
                    raise ValueError(f"Time limit exceed. Collected so far:\n\n{report}")


    def query(self, time_limit_in_seconds: float|None = None, no_exception: bool = False) -> Queryable[IMessage]:
        return Query.en(self._query(time_limit_in_seconds, no_exception))

    def wait_for_confirmation(self,
                              message: IMessage,
                              _type: Type[T] = IMessage,
                              time_limit_in_seconds: float|None = None,
                              no_exceptions: bool = False,
                              debugging_print: bool = False
                              ) -> T:
        client = self.clone_client()
        client.set_last_id(message.envelop.id)
        client.set_allowed_types()
        for received in client.query(time_limit_in_seconds, no_exceptions):
            is_confirmation = received.is_confirmation_of(message)
            if debugging_print:
                logger.info(f"Received {received}, is_confirmation {is_confirmation}")
            if is_confirmation:
                if not isinstance(received, _type):
                    raise ValueError(f"Expecting type {_type}, but was confirmed by {received}")
                return received


    def run_synchronously(self, message: IMessage, _type: Type[T] = IMessage, time_limit_in_seconds: float|None = None) -> T:
        self.push(message)
        return self.wait_for_confirmation(message, _type, time_limit_in_seconds)

    def scroll_to_end(self):
        last = self.tail(1)
        if len(last) == 0:
            self.set_last_id(None)
        else:
            self.set_last_id(last[-1].envelop.id)

    @staticmethod
    def default():
        from ...app.messages import AvatarMessagingService, AvatarMessageRepository
        service = AvatarMessagingService(ttl_in_seconds=None)
        repo = AvatarMessageRepository(service)
        return AvatarClient(repo, 'default')