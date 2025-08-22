import queue
import threading
from typing import Iterable
from ..stream import StreamClient, IMessage
from ..rules import Rule
from .rule_processor import RuleProcessor
from .processing_event import ProcessingEvent
from ..rules import IService


class RuleGroupProcessor:
    def __init__(self,
                 client: StreamClient,
                 rules: Iterable[Rule],
                 event_queue: queue.Queue
                 ):
        self.rules = tuple(rules)
        host = self.rules[0].host_object
        for r in self.rules:
            if r.host_object is not host:
                raise ValueError("All rules must have the same host_object")
        self.host_object = host
        self.client = client
        self._queue = queue.Queue()
        self._event_queue = event_queue
        self._stop_event = threading.Event()


    def put(self, message: IMessage):
        self._queue.put(message)

    def stop(self):
        self._stop_event.set()
        self._queue.put(None)  # unblock get()

    def run(self):
        if isinstance(self.host_object, IService):
            self.host_object.set_client(self.client)
        while not self._stop_event.is_set():
            message: IMessage = self._queue.get()
            if message is None:
                break

            for rule in self.rules:
                if not rule.input.check_incoming(message):
                    continue

                self._event_queue.put(ProcessingEvent(ProcessingEvent.Type.Accepted, message, rule.name))

                runner = RuleProcessor(message, self._event_queue, self.client, rule)
                if rule.asynchronous:
                    threading.Thread(target=runner.run, daemon=True).start()
                else:
                    runner.run()

