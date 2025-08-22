from threading import Lock
from typing import Optional, List, Dict
from .message import IMessage
from .stream import Stream

class TestStream(Stream):
    """
    A thread-safe stream with optional capacity.
    When the number of messages exceeds 2 * capacity, the stream is pruned to capacity.
    """
    def __init__(self, capacity: Optional[int] = None) -> None:
        self.capacity: Optional[int] = capacity
        self.messages: List[IMessage] = []
        self.id_to_index: Dict[str, int] = {}
        self._lock: Lock = Lock()


    def __getstate__(self):
        state = self.__dict__.copy()
        del state['_lock']
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        self._lock = Lock()

    def ready(self):
        pass

    def put(self, message: IMessage) -> None:
        """
        Add a message to the stream. If capacity is set and the number of messages exceeds
        twice the capacity, prune the oldest messages back to capacity.
        """
        if not isinstance(message, IMessage):
            raise ValueError("Only IMessage can be put to the stream")

        with self._lock:
            # Append message and index
            self.id_to_index[message.envelop.id] = len(self.messages)
            self.messages.append(message)

            # Prune if above threshold
            if self.capacity is not None and len(self.messages) > 2 * self.capacity:
                # Calculate how many to remove
                to_remove = len(self.messages) - self.capacity
                # Drop the oldest messages
                self.messages = self.messages[to_remove:]
                # Rebuild the id-to-index mapping
                self.id_to_index = {msg.envelop.id: idx for idx, msg in enumerate(self.messages)}


    def get(self, last_id: Optional[str] = None, count: Optional[int] = None, types: tuple[type,...]|None = None) -> List[IMessage]:
        """
        Retrieve messages after the given last_id. Returns up to 'count' messages,
        or all remaining if count is None.
        """
        with self._lock:
            # Determine start index
            if last_id is None:
                start = 0
            elif last_id not in self.id_to_index:
                start = 0
            else:
                start = self.id_to_index[last_id] + 1

            # Slice messages and return a new list
            if count is None:
                base = self.messages[start:]
            else:
                base = self.messages[start:start + count]

            if types is None:
                return base
            else:
                return [m for m in base if isinstance(m, types)]


    def get_tail(self, count: int, types: tuple[type,...]|None = None) -> list[IMessage]:
        with self._lock:
            base = self.messages[-count:]
            if types is None:
                return base
            return [m for m in base if isinstance(m, types)]

    def get_last_message_id(self) -> str|None:
        if len(self.messages) == 0:
            return None
        return self.messages[-1].envelop.id