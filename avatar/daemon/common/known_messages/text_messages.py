from typing import TypeVar, Generic
from ....messaging import IMessage
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from grammatron import Utterance, UtterancesSequence, DubParameters


def _prettify_string(s):
    s = s.strip()
    s = s[0].upper() + s[1:]
    if s[-1] not in {'.', '!', '?'}:
        s += '.'
    return s


def _unwrap(element: str | Utterance | UtterancesSequence, parameters: DubParameters,
            array: list[str]):
    if isinstance(element, str):
        array.append(element)
    elif isinstance(element, Utterance):
        array.append(element.to_str(parameters))
    elif isinstance(element, UtterancesSequence):
        for component in element.utterances:
            _unwrap(component, parameters, array)
    else:
        raise TypeError("Expected string, Utterance or UtterancesSequence")


def extract_text(argument: str | Utterance | UtterancesSequence, parameters: DubParameters):
    text = []
    _unwrap(argument, parameters, text)
    return ' '.join(_prettify_string(s) for s in text)



@dataclass
class TextEvent(IMessage):
    text: str|Utterance
    user: str|None = None
    file_id: str|None = None


    def get_text(self, spoken: bool) -> str:
        return extract_text(
            self.text,
            DubParameters(spoken)
        )


@dataclass
class TextCommand(IMessage):
    text: str|Utterance|UtterancesSequence
    user: str|None = None
    language: str|None = None
    character: str|None = None

    def get_text(self, spoken: bool) -> str:
        return extract_text(self.text, DubParameters(spoken, self.language))


@dataclass
class InternalTextCommand(IMessage):
    text: str|Utterance|UtterancesSequence
    user: str|None = None
    language: str|None = None
    character: str|None = None

    def get_text(self, spoken: bool) -> str:
        return extract_text(self.text, DubParameters(spoken, self.language))


