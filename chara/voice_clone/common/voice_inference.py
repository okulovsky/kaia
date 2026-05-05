from .voice_train import VoiceModel
from chara.common import CaseCollection, BrainBoxCasePipeline, Chara, ICase
from abc import ABC, abstractmethod
from brainbox import BrainBox
from copy import copy
from pathlib import Path
from dataclasses import dataclass


@dataclass
class VoiceInferenceCase(ICase):
    inference: 'VoiceInference'
    model: VoiceModel
    text: str
    result: Path|None = None


class VoiceInference(ABC):
    Case = VoiceInferenceCase
    @abstractmethod
    def create_task(self, model: VoiceModel, text: str) -> BrainBox.Task:
        pass

    def get_metadata(self) -> dict:
        return copy(self.__dict__)


    @staticmethod
    def _create_task(case: VoiceInferenceCase) -> BrainBox.Task:
        return case.inference.create_task(case.model, case.text)


    @staticmethod
    def pipeline(cases: CaseCollection[VoiceInferenceCase]) -> CaseCollection[VoiceInferenceCase]:
        pipe = BrainBoxCasePipeline(VoiceInference._create_task, 'result')
        result = Chara.call(pipe)(cases)
        return result
