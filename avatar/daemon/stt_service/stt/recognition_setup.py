from typing import Any, Union
from ...common import IMessage, SoundEvent
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from brainbox import BrainBox
from grammatron import Utterance
from ..rhasspy_training import RhasspyHandler
from abc import ABC, abstractmethod

class IPostprocessor(ABC):
    @abstractmethod
    def postprocess(self, result):
        pass

@dataclass
class STTCommand(IMessage):
    file: str
    setup: Union['IRecognitionSetup'] = None
    language: str|None = None


@dataclass
class RecognitionContext:
    command: STTCommand
    rhasspy_handlers: dict[str, RhasspyHandler] = field(default_factory=dict)


@dataclass
class STTConfirmation(IMessage):
    recognition: str|Utterance|None
    meta: Any = None
    error: Any = None


class IRecognitionSetup(IMessage, ABC):
    @abstractmethod
    def create_task_and_postprocessor(self, context: RecognitionContext) -> tuple[BrainBox.Task, IPostprocessor]:
        pass







