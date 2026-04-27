import threading
from datetime import datetime, timedelta
from .avatar_message import AvatarMessage


class Queue:
    def __init__(self, ttl_in_seconds: float|None):
        self.ttl_in_seconds = ttl_in_seconds
        self._messages: list[AvatarMessage] = []
        self._offset: int = 0
        self._lock = threading.Lock()

    def add(self, message: AvatarMessage):
        """
        Adds a message to the queue.
        Removes from the queue all the messages older than ttl.
        """
        with self._lock:
            if self.ttl_in_seconds is not None:
                cutoff = datetime.now() - timedelta(seconds=self.ttl_in_seconds)
                while self._messages and self._messages[0].envelop.timestamp < cutoff:
                    self._messages.pop(0)
                    self._offset += 1
            self._messages.append(message)

    def get_index(self, id: str) -> int | None:
        """
        Quickly finds the index of the message with the given id in the queue.
        Returns an absolute index stable across TTL removals.
        """
        with self._lock:
            for i, m in enumerate(self._messages):
                if m.envelop.id == id:
                    return self._offset + i
            return None

    @property
    def first_index(self) -> int:
        """
        Returns the absolute index of the first available message (i.e. the offset).
        """
        with self._lock:
            return self._offset

    def __len__(self) -> int:
        """
        Returns the absolute upper bound (offset + current count).
        """
        with self._lock:
            return self._offset + len(self._messages)

    def __getitem__(self, index: int) -> AvatarMessage:
        """
        Returns the message at the given absolute index.
        """
        with self._lock:
            return self._messages[index - self._offset]

    def find_index_from_timestamp(self, timestamp: datetime) -> int:
        """Returns the absolute index of the first message with timestamp >= given value."""
        with self._lock:
            for i, m in enumerate(self._messages):
                if m.envelop.timestamp >= timestamp:
                    return self._offset + i
            return self._offset + len(self._messages)
