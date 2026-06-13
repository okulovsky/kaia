from dataclasses import dataclass
from pathlib import Path
from .voice_train import VoiceModel
from abc import ABC, abstractmethod
from brainbox import BrainBox
from chara.common import CaseCollection, BrainBoxCasePipeline, ICase, Chara


@dataclass
class RevoiceCase(ICase):
    file: Path
    revoice: 'Revoice'
    model: VoiceModel
    result: Path|None = None


class Revoice(ABC):
    Case = RevoiceCase

    @abstractmethod
    def create_task(self, model: VoiceModel, file: Path) -> BrainBox.Task:
        pass

    @staticmethod
    def _create_task(case: RevoiceCase) -> BrainBox.Task:
        return case.revoice.create_task(case.model, case.file)

    @staticmethod
    def pipeline(cases: CaseCollection[RevoiceCase]) -> CaseCollection[RevoiceCase]:
        pipeline = BrainBoxCasePipeline(
            Revoice._create_task,
            'result',
            result_to_file=True
        )
        return Chara.call(pipeline)(cases)
