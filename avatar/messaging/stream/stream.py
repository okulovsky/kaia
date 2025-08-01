import time
from abc import ABC, abstractmethod
from .message import IMessage
from typing import TypeVar, Type
import time
from yo_fluq import Queryable, Query


T = TypeVar('T', bound=IMessage)


class StreamClient:
    def __init__(self, stream: 'Stream', last_id: str|None):
        self.stream = stream
        self.last_id = last_id

    def pull(self, count: int|None = None) -> list[IMessage]:
        data = self.stream.get(self.last_id, count)
        if len(data) > 0:
            self.last_id = data[-1].envelop.id
        return data

    def put(self, message: IMessage) -> IMessage:
        self.stream.put(message)
        return message

    def clone(self) -> 'StreamClient':
        return StreamClient(self.stream, self.last_id)


    def wait_for_confirmation(self, message: IMessage, _type: Type[T] = IMessage, time_limit_in_seconds: float|None = None) -> T:
        client = self.stream.create_client(message.envelop.id)
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

    def _query(self, time_limit_in_seconds: float|None = None):
        begin = time.monotonic()
        collected_so_far = []
        while True:
            result = self.pull(1)
            collected_so_far.extend(result)
            yield from result
            if time_limit_in_seconds is not None and (time.monotonic() - begin) > time_limit_in_seconds:
                raise ValueError(f"Time limit exceed. Collected so far:\n{collected_so_far}")
            time.sleep(0.01)

    def query(self, time_limit_in_seconds: float|None = None) -> Queryable[IMessage]:
        return Query.en(self._query(time_limit_in_seconds))






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

    def create_client(self, last_id: str|None = None) -> StreamClient:
        return StreamClient(self, last_id)


