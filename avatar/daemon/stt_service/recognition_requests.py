from typing import Any
from dataclasses import dataclass
from grammatron import TemplateBase, Utterance
from ..common import IMessage
from .rhasspy_training import IntentsPack

MAIN_CONTEXT = 'CORE'


@dataclass
class STTTrainingCommand(IMessage):
    packs: list[IntentsPack]


class IRecognitionRequest(IMessage):
    pass


@dataclass
class TemplatesRecognitionRequest(IRecognitionRequest):
    context: str = MAIN_CONTEXT


@dataclass
class FreeSpeechRecognitionRequest(IRecognitionRequest):
    language: str|None = None
    prompt: str|None = None
    template: TemplateBase|None = None


@dataclass
class RecognitionEvent(IMessage):
    file_id: str
    recognition: str|Utterance|None
    error: Any = None
