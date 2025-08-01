from typing import TypeVar, Generic
from ....messaging import IMessage
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from grammatron import Utterance, UtterancesSequence, DubParameters


class ITextMessage(ABC):
    @abstractmethod
    def get_text(self, spoken: bool, language: str|None) -> str:
        pass

@dataclass
class TextInfo:
    speaker: str
    language: str


TTextMessage = TypeVar('TTextMessage', bound=ITextMessage)

@dataclass
class PlayableTextMessage(IMessage, Generic[TTextMessage]):
    text: TTextMessage
    info: TextInfo = field(metadata=dict(json=True))

@dataclass
class UtteranceEvent(IMessage, ITextMessage):
    utterance: Utterance

    def get_text(self, spoken: bool, language: str|None) -> str:
        return self.utterance.to_str(DubParameters(spoken, language))

@dataclass
class TextEvent(IMessage, ITextMessage):
    text: str
    def get_text(self, spoken: bool, language: str|None) -> str:
        return self.text


class UtteranceSequenceCommand(IMessage, ITextMessage):
    def __init__(self, content: UtterancesSequence|Utterance|str):
        if isinstance(content, UtterancesSequence):
            self.utterances_sequence = content
        else:
            self.utterances_sequence = UtterancesSequence(content)

    def _prettify_string(self, s):
        s = s.strip()
        s = s[0].upper() + s[1:]
        if s[-1] not in {'.', '!', '?'}:
            s += '.'
        return s

    def get_text(self, spoken: bool, language: str|None) -> str:
        texts = []
        for component in self.utterances_sequence.utterances:
            if isinstance(component, str):
                texts.append(component)
            elif isinstance(component, Utterance):
                texts.append(component.to_str(DubParameters(spoken, language)))
        texts = [self._prettify_string(s) for s in texts]
        return ' '.join(texts)

@dataclass
class TextCommand(IMessage, ITextMessage):
    text: str

    def get_text(self, spoken: bool, language: str|None) -> str:
        return self.text



