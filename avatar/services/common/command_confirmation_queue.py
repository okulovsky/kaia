from typing import TypeVar, Generic, Iterable
from dataclasses import dataclass
from ...messaging import IMessage

TCommand = TypeVar("TCommand", bound=IMessage)
TConfirmation = TypeVar("TConfirmation", bound=IMessage)

@dataclass
class QueueElement(Generic[TCommand, TConfirmation]):
    command: TCommand
    confirmation: TConfirmation|None = None

class CommandConfirmationQueue(Generic[TCommand, TConfirmation]):
    Element = QueueElement

    def __init__(self):
        self.queue: list[QueueElement[TCommand, TConfirmation]] = []

    def start_tracking(self, commands: Iterable[TCommand]):
        for command in commands:
            self.queue.append(QueueElement(command))

    def track(self, confirmation: TConfirmation):
        if confirmation.envelop.confirmation_for is not None:
            for index in range(len(self.queue)):
                if confirmation.is_confirmation_of(self.queue[index].command):
                    self.queue[index].confirmation = confirmation

    def get_processed_head_length(self) -> int:
        for i in range(len(self.queue)):
            if self.queue[i].confirmation is None:
                return i
        return len(self.queue)

    def deque(self) -> QueueElement[TCommand, TConfirmation]:
        if len(self.queue) == 0:
            raise ValueError("Queue is empty")
        if self.queue[0].confirmation is None:
            raise ValueError("Cannot dequeue non-processed element")
        return self.queue.pop(0)

