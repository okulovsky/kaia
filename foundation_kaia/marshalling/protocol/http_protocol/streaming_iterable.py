import queue
from collections.abc import Iterator


class StreamingIterable:
    def __init__(self):
        self._queue = queue.Queue()

    def _put(self, chunk: bytes):
        self._queue.put(chunk)

    def _close(self):
        self._queue.put(None)

    def __iter__(self) -> Iterator[bytes]:
        while True:
            chunk = self._queue.get()
            if chunk is None:
                return
            yield chunk
