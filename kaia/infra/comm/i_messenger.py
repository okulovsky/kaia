from typing import *
from datetime import datetime
import dataclasses


@dataclasses.dataclass
class Message:
     id: str
     payload: Any
     date_posted: Optional[datetime]
     open: bool
     result: Any
     tags: Tuple


class MessengerQuery:
    def __init__(self,
                 id: Optional[str] = None,
                 open: Optional[bool] = None,
                 tags: Union[None, str, Iterable[Union[str,Iterable[str]]]] = None,
        ):
        self.id = id
        self.open = open
        self.tags = tags

    def query(self, messenger: 'IMessenger') -> List[Message]:
        return messenger.read(self)

    def query_single(self, messenger: 'IMessenger') -> Message:
        result = self.query(messenger)
        if len(result)!=1:
            raise ValueError(f"Request for id `{self.id}`, tags `{self.tags}`, open `{self.open}` returned {len(result)} tasks, 1 was expected")
        return result[0]

    def query_count(self, messenger: 'IMessenger') -> int:
        return len(self.query(messenger))


class IMessenger:
    Query = MessengerQuery

    def add(self, payload: Any, *tags: str) -> str:
        raise NotImplementedError()

    def read(self, query: Optional[MessengerQuery] = None) -> List[Message]:
        raise NotImplementedError()

    def close(self, id: str, payload: Any):
        raise NotImplementedError()

    def read_all_and_close(self, tags: Union[None, str, Iterable[str]] = None) -> List[Message]:
        tasks = self.read(MessengerQuery(tags = tags, open=True))
        for t in tasks:
            self.close(t.id, None)
        return tasks

