from __future__ import annotations

from threading import Lock

from .message_record import MessageRecord
from .message_store import LastMessageNotFoundException



class InMemoryStore:
    def __init__(self, capacity: int = 1000):
        if capacity <= 0:
            raise ValueError("capacity must be > 0")
        self.capacity = capacity
        self._index_to_message: dict[int, MessageRecord] = dict()
        self._id_to_index: dict[str, int] = dict()
        self._position = 0
        self._lock = Lock()



    def add(self, msg: MessageRecord) -> None:
        if msg.message_id is None:
            raise ValueError("MessageRecord.message_id must be set before caching")

        with self._lock:
            if msg.message_id in self._id_to_index:
                raise ValueError("Duplicating message_id")

            while len(self._index_to_message) >= self.capacity:
                to_delete = self._position - len(self._index_to_message)
                del self._id_to_index[self._index_to_message[to_delete].message_id]
                del self._index_to_message[to_delete]

            self._id_to_index[msg.message_id] = self._position
            self._index_to_message[self._position] = msg
            self._position += 1

    def last_id(self, session: str | None) -> str | None:
        with self._lock:
            for index in range(self._position-1, -1, -1):
                if index not in self._index_to_message:
                    return None
                message = self._index_to_message[index]
                if session is None or message.session == session:
                    return message.message_id
            return None

    def tail(
        self,
        session: str | None,
        count: int | None,
        types: list[str] | None,
        except_types: list[str] | None,
    ) -> list[MessageRecord]:
        raise NotImplementedError()

    def get(
        self,
        session: str | None,
        count: int | None,
        last_message_id: str | None,
        types: list[str] | None,
        except_types: list[str] | None,
    ) -> list[MessageRecord]:
        if last_message_id is None:
            raise LastMessageNotFoundException('NONE')
        with self._lock:
            if last_message_id not in self._id_to_index:
                raise LastMessageNotFoundException(last_message_id)
            start_index = self._id_to_index[last_message_id] + 1
            result = []
            for index in range(start_index, self._position):
                message = self._index_to_message[index]
                if self._match(message, session, types, except_types):
                    result.append(message)

        if count is not None:
            if count <= 0:
                return []
            return result[:count]
        return result

    @staticmethod
    def _match(
        m: MessageRecord,
        session: str | None,
        types: list[str] | None,
        except_types: list[str] | None,
    ) -> bool:
        if session is not None and m.session != session:
            return False

        mt = m.message_type or ""

        # types: как в SQL `like "%suf"` -> endswith(suf)
        if types:
            ok = False
            for suf in types:
                if mt.endswith(suf):
                    ok = True
                    break
            if not ok:
                return False

        if except_types:
            for suf in except_types:
                if mt.endswith(suf):
                    return False

        return True


    class Factory:
        def __init__(self, capacity: int):
            self.capacity = capacity

        def __call__(self, session):
            return InMemoryStore(self.capacity)