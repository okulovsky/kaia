import traceback
from typing import *
from ..stream import IMessage, StreamClient
from ..rules import Rule
from .processing_event import ProcessingEvent
from queue import Queue
from dataclasses import dataclass

@dataclass
class ErrorEvent(IMessage):
    exception_type: str
    exception_message: str
    source: str
    traceback: str

class RuleProcessor:
    def __init__(self, message: IMessage, event_queue: Queue, client: StreamClient, rule: Rule):
        self.message = message
        self.event_queue = event_queue
        self.client = client
        self.rule = rule


    def run(self):
        raw_result = None
        parsed_result = None

        try:
            raw_result = self.rule.service(self.message)

            if isinstance(raw_result, IMessage):
                parsed_result = (raw_result,)
            elif raw_result is None:
                parsed_result = ()
            else:
                try:
                    parsed_result = list(raw_result)
                except:
                    raise TypeError(f"Handler {self.rule.service.__name__} returned invalid type: {type(raw_result)}")

            for message in parsed_result:
                if not isinstance(message, IMessage):
                    f"Handler {self.rule.service.__name__} returned invalid type: {type(message).__name__}, "

                if self.rule.outputs is not None:
                    try:
                        is_right_instance = isinstance(message, self.rule.outputs)
                    except:
                        raise ValueError(f"Something wrong with the outputs' types {self.rule.outputs} by rule {self.rule.name}")

                    if not is_right_instance:
                        raise TypeError(
                            f"Handler {self.rule.service.__name__} returned unexpected type: {type(message).__name__}, "
                            f"expected {self.rule.outputs}"
                        )

                if message.envelop.reply_to is None:
                    message.as_reply_to(self.message)
                message.as_from_publisher(self.rule.name)
                self.client.put(message)

        except:
            tb = traceback.format_exc()
            self.event_queue.put(ProcessingEvent(ProcessingEvent.Type.Error, self.message, self.rule.name, parsed_result, tb))
            return

        self.event_queue.put(ProcessingEvent(ProcessingEvent.Type.Finished, self.message, self.rule.name, parsed_result))
