import datetime
import threading
import time
from collections import defaultdict
from .rule_group_processor import RuleGroupProcessor
from ..stream import StreamClient, IStreamClient
from ..rules import RulesCollection
import queue
from .filters import *
from dataclasses import dataclass
from datetime import datetime
from threading import Thread

@dataclass
class AvatarDebugReport:
    messages: tuple[IMessage,...]
    duration: float

@dataclass
class TickEvent(IMessage):
    time: datetime




@dataclass
class ExceptionEvent(IMessage):
    source: str
    traceback: str



class AvatarDaemon:
    def __init__(self,
                 client: StreamClient,
                 time_tick_interval_in_seconds: float|None = None,
                 add_error_events: bool = False,
                 reporting_client: IStreamClient|None = None
                 ):
        self.client = client
        self.rules = RulesCollection()
        self._stop_flag = threading.Event()
        self.time_tick_interval_in_seconds = time_tick_interval_in_seconds
        self.last_time_tick: TickEvent|None = None
        self.add_error_events = add_error_events
        self.reporting_client = reporting_client

    def __getstate__(self):
        state = self.__dict__.copy()
        del state['_stop_flag']
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        self._stop_flag = threading.Event()

    def stop(self):
        self._stop_flag.set()

    def run(self, filters: list[IProcessingFilter]|None = None):
        if filters is None:
            filters = []

        self.client.initialize()
        if self.reporting_client is not None:
            self.reporting_client.initialize()

        # Group rules by host_object
        grouped = defaultdict(list)
        for rule in self.rules.rules:
            key = rule.host_object if rule.host_object is not None else id(rule)
            grouped[key].append(rule)

        self._event_queue = queue.Queue()

        # Make RuleProcessors
        self.processors = [
            RuleGroupProcessor(self.client, rules_for_host, self._event_queue)
            for rules_for_host in grouped.values()
        ]

        self._threads: list[threading.Thread] = []

        for processor in self.processors:
            t = threading.Thread(target=processor.run, daemon=True)
            t.start()
            self._threads.append(t)

        try:
            while not self._stop_flag.is_set():
                if self.time_tick_interval_in_seconds is not None:
                    current = datetime.now()
                    if self.last_time_tick is None or (current - self.last_time_tick.time).total_seconds() > self.time_tick_interval_in_seconds:
                        self.last_time_tick = TickEvent(current)
                        self.client.put(self.last_time_tick)

                messages = self.client.pull()
                for message in messages:
                    self._event_queue.put(ProcessingEvent(ProcessingEvent.Type.Received, message))
                    for processor in self.processors:
                        processor.put(message)

                exit = False
                for filter in filters:
                    if filter.should_stop_on_queue(messages):
                        exit = True
                while not self._event_queue.empty():
                    event: ProcessingEvent = self._event_queue.get()
                    if self.reporting_client is not None:
                        self.reporting_client.put(event)
                    if self.add_error_events and event.type == ProcessingEvent.Type.Error:
                        self.client.put(ExceptionEvent(event.rule_name, event.exception))
                    for filter in filters:
                        if filter.should_stop_on_event(event):
                            exit = True
                if exit:
                    break
                time.sleep(0.01)
        finally:
            for processor in self.processors:
                processor._stop_event.set()

    def __call__(self):
        self.run()

    def run_in_thread(self):
        Thread(target=self.run, daemon=True).start()

    def debug(self, messages, filters: list[IProcessingFilter]) -> AvatarDebugReport:
        for message in messages:
            self.client.put(message)
        start = time.perf_counter()
        client = self.client.clone()
        self.run(filters)
        end = time.perf_counter()
        return AvatarDebugReport(
            tuple(client.pull()),
            end-start
        )

    def debug_and_stop_by_count(self, count: int, *messages: IMessage) -> AvatarDebugReport:
        return self.debug(
            messages,
            [
                MaxProcessedMessagesFilter(count),
                PrintingFilter(),
                ExceptionFilter(),
                MaxTimeFilter(1),
            ]
        )

    def debug_and_stop_by_message_type(self, type, *messages: IMessage) -> AvatarDebugReport:
        return self.debug(
            messages,
            [
                MessageFoundFilter(type),
                PrintingFilter(),
                ExceptionFilter(),
                MaxTimeFilter(1),
            ])

    def debug_and_stop_by_empty_queue(self, *messages: IMessage, time = 0.1) -> AvatarDebugReport:
        return self.debug(
            messages,
            [
                QueueEmptyFilter(time),
                PrintingFilter(),
                ExceptionFilter(),
                MaxTimeFilter(1)
            ])

    def debug_and_stop_by_all_confirmed(self, *messages: IMessage):
        return self.debug(
            messages,
            [
                AllConfirmedFilter(messages),
                PrintingFilter(),
                ExceptionFilter(),
                MaxTimeFilter(1)
            ]
        )