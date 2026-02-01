from .message_record import MessageRecord
from .message_store import IMessageStore, LastMessageNotFoundException
from .sql_message_store import SqlMessageStore
from .in_memory_store import InMemoryStore

class CompositeStore(IMessageStore):
    def __init__(self, fast, slow):
        self.fast = fast
        self.slow = slow

    def add(self, msg: MessageRecord) -> None:
        # Durable first: never keep in RAM something that failed to persist
        self.slow.add(msg)
        self.fast.add(msg)

    def last_id(self, session: str | None) -> str | None:
        mid = self.fast.last_id(session)
        if mid is not None:
            return mid
        return self.slow.last_id(session)

    def get(
        self,
        session: str | None,
        count: int | None,
        last_message_id: str | None,
        types: list[str] | None,
        except_types: list[str] | None,
    ):
        try:
            return self.fast.get(session, count, last_message_id, types, except_types)
        except LastMessageNotFoundException:
            return self.slow.get(session, count, last_message_id, types, except_types)
        except Exception as ex:
            raise ValueError(f"Unexpected exception: {type(ex)}") from ex

    def tail(
        self,
        session: str | None,
        count: int | None,
        types: list[str] | None,
        except_types: list[str] | None,
    ):
        return self.slow.tail(session, count, types, except_types)


    class Factory:
        def __init__(self, capacity: int):
            self.capacity = capacity

        def __call__(self, session):
            return CompositeStore(
                InMemoryStore(self.capacity),
                SqlMessageStore(session)
            )