from abc import ABC, abstractmethod
from avatar.messaging import IMessage, TimerEvent
from avatar.daemon import UtteranceEvent, TextEvent
from typing import Any



class IKaiaInputTransformer(ABC):
    @abstractmethod
    def transform(self, input: IMessage) -> Any:
        pass


class DefaultKaiaInputTransformer(IKaiaInputTransformer):
    def __init__(self, allow_timer: bool):
        self.allow_timer = allow_timer

    def transform(self, input: IMessage) -> Any:
        if isinstance(input, UtteranceEvent):
            return input.utterance
        if isinstance(input, TextEvent):
            return input.text
        if self.allow_timer and isinstance(input, TimerEvent):
            return input
        return None

