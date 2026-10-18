from typing import Any
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from brainbox import BrainBox
from grammatron import Utterance
from ..rhasspy_training import RhasspyHandler

class IPostprocessor(ABC):
    @abstractmethod
    def postprocess(self, result) -> 'RecognitionResult':
        pass


@dataclass
class RecognitionContext:
    file: str
    language: str|None = None
    rhasspy_handlers: dict[str, RhasspyHandler] = field(default_factory=dict)


@dataclass
class RecognitionResult:
    recognition: str|Utterance|None
    meta: Any = None
    error: Any = None


class IRecognitionSetup(ABC):
    @abstractmethod
    def create_task_and_postprocessor(self, context: RecognitionContext) -> tuple[BrainBox.Task, IPostprocessor]:
        pass
