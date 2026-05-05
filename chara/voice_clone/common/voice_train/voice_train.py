from typing import Iterable
from abc import ABC, abstractmethod
from yo_fluq import FileIO
from hashlib import md5
import subprocess

from chara.common import CaseCollection
from .small_classes import *
from .pipeline import pipeline




class VoiceTrain(ABC):
    Case = VoiceTrainCase

    def compute_hash(self, source_files: Iterable[Path]) -> str:
        source_files = list(sorted(source_files))
        hash = []
        for source in source_files:
            data = FileIO.read_bytes(source)
            model_name = md5(data).hexdigest()[:24]
            hash.append(model_name)
        result = '/'.join(hash)
        return md5(result.encode()).hexdigest()[:24]

    def get_metadata_extensions(self) -> tuple[str,...]:
        return ()

    def aggregate_metadata(self, data: list[dict]) -> dict:
        return {}

    @abstractmethod
    def create_train_task_and_reference(
            self,
            samples: list[Path],
            samples_metadata: list[dict],
            metadata: VoiceTrainMetadata|None = None
    ) -> tuple[BrainBox.Task, VoiceModel]:
        pass


    def recode_in_proper_format(self, file: Path, folder: Path) -> str:
        target_path = folder/(file.name.split('.')[0]+'.wav')
        subprocess.call([
            'ffmpeg',
            '-i',
            str(file),
            '-y',
            str(target_path)
        ])
        if not target_path.is_file():
            raise ValueError(f"Conversion failed on file {file}.")
        return target_path.name

    @abstractmethod
    def requires_train_single_file_with_extension(self) -> str | None:
        pass

    @staticmethod
    def pipeline(cases: CaseCollection[VoiceTrainCase]) -> CaseCollection[VoiceTrainCase]:
        return pipeline(cases)

















