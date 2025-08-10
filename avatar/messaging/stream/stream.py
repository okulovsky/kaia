import time
from abc import ABC, abstractmethod
from .message import IMessage
from typing import TypeVar, Type
from avatar.messaging.amenities import ThreadCollection
import time
from yo_fluq import Queryable, Query
from loguru import logger


T = TypeVar('T', bound=IMessage)

class _ScrollClientOnInit:
    pass

class StreamClient:
    def __init__(self, stream: 'Stream', last_id: str|None, name: str|None = None, debug: bool = False):
        self._stream = stream
        self.last_id = last_id
        self.name = name
        self.debug = debug

    def with_name(self, new_name: str) -> 'StreamClient':
        self.name = new_name
        return self

    def with_debug(self) -> 'StreamClient':
        self.debug = True
        return self


    def pull(self, count: int|None = None) -> list[IMessage]:
        data = self._stream.get(self.last_id, count)
        if len(data) > 0:
            self.last_id = data[-1].envelop.id
            if self.debug:
                logger.info(f"Client {self.name} pulled {len(data)} messages and is now at {self.last_id}\t"+' '.join(f'{m.envelop.id}/{type(m).__name__}' for m in data))
        return data

    def put(self, message: IMessage) -> IMessage:
        self._stream.put(message)
        if self.debug:
            logger.info(f"Client {self.name} pushed {message.envelop.id}/{type(message).__name__}")
        return message

    def clone(self, new_name: str|None = None) -> 'StreamClient':
        return StreamClient(self._stream, self.last_id, self.name if new_name is None else new_name, self.debug)

    def wait_for_confirmation(self, message: IMessage, _type: Type[T] = IMessage, time_limit_in_seconds: float|None = None) -> T:
        client = self._stream.create_client(message.envelop.id)
        begin = time.monotonic()
        collected_so_far = []
        while True:
            for produced_message in client.pull():
                if produced_message.is_confirmation_of(message):
                    if not isinstance(produced_message, _type):
                        raise ValueError(f"Expecting type {_type}, but was confirmed by {produced_message}")
                    return produced_message
                collected_so_far.append(produced_message)
            if time_limit_in_seconds is not None and time.monotonic() - begin > time_limit_in_seconds:
                raise ValueError(f"Time limit exceeded. Collected so far\n{collected_so_far}")
            time.sleep(0.01)

    def run_synchronously(self, message: IMessage, _type: Type[T] = IMessage, time_limit_in_seconds: float|None = None) -> T:
        self.put(message)
        return self.wait_for_confirmation(message, _type, time_limit_in_seconds)

    def _query(self, time_limit_in_seconds: float|None = None, no_exception: bool = False):
        begin = time.monotonic()
        collected_so_far = []
        while True:
            result = self.pull(1)
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
                            report = ThreadCollection.just_print(collected_so_far, True)
                        except:
                            report = 'Errors when generating the report'
                    raise ValueError(f"Time limit exceed. Collected so far:\n\n{report}")
            time.sleep(0.01)

    def query(self, time_limit_in_seconds: float|None = None, no_exception: bool = False) -> Queryable[IMessage]:
        return Query.en(self._query(time_limit_in_seconds, no_exception))

    def scroll_to_end(self) -> 'StreamClient':
        self.last_id = self._stream.get_last_message_id()
        return self

    def initialize(self):
        self._stream.ready()




class Stream(ABC):
    @abstractmethod
    def put(self, message: IMessage):
        pass

    @abstractmethod
    def get(self, last_id: str|None = None, count: int|None = None) -> list[IMessage]:
        pass

    @abstractmethod
    def ready(self):
        pass

    @abstractmethod
    def get_last_message_id(self) -> str|None:
        pass

    def create_client(self, last_id: str|None = None) -> StreamClient:
        return StreamClient(self, last_id)


