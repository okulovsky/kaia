from abc import ABC, abstractmethod
from typing import *
from ..dubbing_service import TextLike, DubbingServiceOutput
from ..recognition_service import RecognitionSettings
from brainbox import File
from kaia.dub import Template, IntentsPack
from pathlib import Path


class IAvatarApi(ABC):
    @abstractmethod
    def dub(self, text: TextLike) -> DubbingServiceOutput:
        pass


    @abstractmethod
    def dub_get_result(self, job_id: str) -> File:
        pass

    @abstractmethod
    def image_get_new(self, empty_image_if_none = True) -> Optional[File]:
        pass

    @abstractmethod
    def image_get_current(self, empty_image_if_none = True) -> Optional[File]:
        pass

    @abstractmethod
    def image_get_empty(self) -> File:
        pass

    @abstractmethod
    def image_report(self, report: str) -> None:
        pass

    @abstractmethod
    def state_change(self, change: dict[str, Any]) -> None:
        pass

    @abstractmethod
    def state_get(self) -> dict[str, Any]:
        pass

    @abstractmethod
    def recognition_train(self, intents: tuple[IntentsPack,...], replies: tuple[Template,...]):
        pass

    @abstractmethod
    def recognition_transcribe(self, file_id: str, settings: RecognitionSettings):
        pass

    @abstractmethod
    def recognition_speaker_fix(self, actual_speaker: str):
        pass

    @abstractmethod
    def recognition_speaker_train(self, media_library_path: Path):
        pass
