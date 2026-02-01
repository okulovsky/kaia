import datetime

from .processing_event import ProcessingEvent, IMessage

class IProcessingFilter:
    def should_stop_on_event(self, event: ProcessingEvent):
        return False

    def should_stop_on_queue(self, messages: list[IMessage]):
        return False

class MaxProcessedMessagesFilter(IProcessingFilter):
    def __init__(self, count: int):
        self.count = count
        self.seen = 0

    def should_stop_on_event(self, event: ProcessingEvent):
        if event.type == ProcessingEvent.Type.Finished:
            self.seen += 1
        return self.seen >= self.count


class MaxTimeFilter(IProcessingFilter):
    def __init__(self, time_in_seconds: float):
        self.time_in_seconds = time_in_seconds
        self.begin = None

    def should_stop_on_queue(self, messages: list[IMessage]):
        if self.begin is None:
            self.begin = datetime.datetime.now()
        delta = (datetime.datetime.now() - self.begin).total_seconds()
        if delta > self.time_in_seconds:
            raise ValueError("Exited by time limit")

class ExceptionFilter(IProcessingFilter):
    def should_stop_on_event(self, event: ProcessingEvent):
        if event.type == ProcessingEvent.Type.Error:
            raise ValueError(f"A handler threw an exception:\n{event.exception}")


class MessageFoundFilter(IProcessingFilter):
    def __init__(self, *expected_messages_types):
        self.expected_messages_types = expected_messages_types

    def should_stop_on_event(self, event: ProcessingEvent):
        return event.type == ProcessingEvent.Type.Received and isinstance(event.message, self.expected_messages_types)


class PrintingFilter(IProcessingFilter):
    def should_stop_on_event(self, ev: ProcessingEvent):
        print(f"{ev.timestamp} {ev.type} {type(ev.message).__name__} {ev.rule_name} {ev.rejection_reason}")
        return False


class QueueEmptyFilter(IProcessingFilter):
    def __init__(self, time_for_queue_to_be_empty: float = 0.1):
        self.time_for_queue_to_be_empty = time_for_queue_to_be_empty
        self.begin = None

    def should_stop_on_queue(self, messages: list[IMessage]):
        if len(messages) > 0:
            self.begin = None
        else:
            if self.begin is None:
                self.begin = datetime.datetime.now()
            else:
                if (datetime.datetime.now() - self.begin).total_seconds() > self.time_for_queue_to_be_empty:
                    return True
        return False


class AllConfirmedFilter(IProcessingFilter):
    def __init__(self, messages: tuple[IMessage,...]):
        self.wait_for = {m.envelop.id for m in messages}

    def should_stop_on_queue(self, messages: list[IMessage]):
        for m in messages:
            if m.envelop.confirmation_for is not None:
                for c in m.envelop.confirmation_for:
                    if c in self.wait_for:
                        self.wait_for.remove(c)
        return len(self.wait_for) == 0
