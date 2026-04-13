import queue


class QueueIterable:
    """Thread-safe iterable backed by a queue. Bridges async WebSocket receives
    to a sync iterable consumed by the service method in a thread executor."""

    def __init__(self):
        self._queue: queue.Queue = queue.Queue()

    def put(self, data):
        self._queue.put(data)

    def end(self):
        self._queue.put(None)

    def __iter__(self):
        return self

    def __next__(self):
        item = self._queue.get()
        if item is None:
            raise StopIteration
        return item
