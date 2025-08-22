from __future__ import annotations
import time
from queue import Queue
from dataclasses import dataclass, field
import threading
from typing import TYPE_CHECKING, Iterable, Any
from .message import IMessage
from .i_stream_client import IStreamClient
import weakref
import sys


if TYPE_CHECKING:
    from .stream import StreamClient



@dataclass
class ClientWorker:
    client: StreamClient
    to_server: Queue = field(default_factory=Queue)
    from_server: Queue = field(default_factory=Queue)
    stop_event: threading.Event = field(default_factory=threading.Event)
    exc: Any = None
    exc_tb: Any = None


    def run(self):
        try:
            while True:
                while not self.to_server.empty():
                    message = self.to_server.get()
                    self.client.put(message)
                messages = self.client.pull()
                for message in messages:
                    self.from_server.put(message)
                if self.stop_event.is_set():
                    break
                time.sleep(0.01)
        except:
            _, e, tb = sys.exc_info()
            self.exc, self.exc_tb = e, tb


class AsyncStreamClient(IStreamClient):
    def __init__(self, client: StreamClient):
        self.client = client.clone()
        self.worker = None

    def initialize(self):
        self.client.initialize()
        self.worker = ClientWorker(self.client)
        threading.Thread(target=self.worker.run, daemon=True).start()
        self._finalizer = weakref.finalize(self, self._cleanup)

    def _cleanup(self):
        if self.worker is not None:
            self.worker.stop_event.set()

    def _check_exception(self):
        if self.worker is not None and self.worker.exc is not None:
            raise self.worker.exc.with_traceback(self.worker.exc_tb)

    def put(self, message: IMessage):
        self._check_exception()
        self.worker.to_server.put(message)


    def pull_all(self) -> Iterable[IMessage]:
        self._check_exception()
        taken = 0
        while not self.worker.from_server.empty():
            message = self.worker.from_server.get()
            yield message
            taken+=1








