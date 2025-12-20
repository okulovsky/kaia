import os
import shutil

from chara.common import ICache, FolderCache, ListCache, BrainBoxCache, logger, BrainBoxUnit
from chara.common.tools import Wav
from typing import Iterable

from abc import ABC, abstractmethod
from typing import Any
from brainbox import BrainBox
from pathlib import Path
from dataclasses import dataclass
from copy import copy

class VoiceModel:
    def get_metadata(self) -> dict:
        return copy(self.__dict__)




class VoiceTrainPreprocessingCache(ICache):
    def __init__(self):
        super().__init__()
        self.recoded = FolderCache()
        self.train_samples = FolderCache()


class VoiceTrainCache(ICache[list[VoiceModel]]):
    def __init__(self, working_folder: Path|None = None):
        super().__init__(working_folder)
        self.preprocessing = ListCache[VoiceTrainPreprocessingCache, None](VoiceTrainPreprocessingCache)
        self.training = BrainBoxCache()

    def read_train_samples(self) -> Wav.List:
        wavs = []
        models = self.read_result()
        for index, model in enumerate(models):
            subcache = self.preprocessing.create_subcache(index)
            for path in subcache.recoded.read_paths():
                wav = Wav.one(path)
                wav.assign_metadata(**model.get_metadata())
                wavs.append(wav)
        return Wav.List(wavs)


@dataclass
class VoiceTrainMetadata:
    model_name: str|None = None
    original_samples_path: Path|None = None



class VoiceTrain(ABC):
    Cache = VoiceTrainCache

    @abstractmethod
    def create_train_task_and_reference(self, samples: list[Path], metadata: VoiceTrainMetadata|None = None) -> tuple[BrainBox.ITask, VoiceModel]:
        pass

    @abstractmethod
    def recode_in_proper_format(self, file: Path, folder: Path):
        pass

    @abstractmethod
    def requires_train_single_file_with_extension(self) -> str | None:
        pass

    @staticmethod
    def _preprocess(cache: VoiceTrainPreprocessingCache, trainer: 'VoiceTrain', source: Path):
        @logger.phase(cache.recoded)
        def _():
            if source.is_file():
                files = [source]
            elif source.is_dir():
                files = list(source.iterdir())
            else:
                raise ValueError(f"{source} is not a file or a directory")
            os.makedirs(cache.recoded.working_folder, exist_ok=True)
            for file in files:
                trainer.recode_in_proper_format(file, cache.recoded.working_folder)
            cache.recoded.finalize()

        @logger.phase(cache.train_samples)
        def _():
            os.makedirs(cache.train_samples.working_folder, exist_ok=True)
            ex = trainer.requires_train_single_file_with_extension()
            if ex is not None and len(cache.recoded.read_paths()) > 1:
                Wav.concat_with_ffmpeg(
                    cache.recoded.read_paths(),
                    cache.train_samples.working_folder/f'sample.{ex}'
                )
            else:
                for path in cache.recoded.read_paths():
                    shutil.copy(path, cache.train_samples.working_folder/path.name)
            cache.train_samples.finalize()

        cache.finalize()

    @staticmethod
    def pipeline(
            cache: VoiceTrainCache,
            trainers: 'VoiceTrain|Iterable[VoiceTrain]',
            sources: Path|str|Iterable[Path]
    ):
        if isinstance(trainers, VoiceTrain):
            trainers = [trainers]

        if isinstance(sources, Path) or isinstance(sources, str):
            sources = [sources]
        else:
            sources = list(sources)

        tasks = []
        models = []
        idx = 0
        for trainer_index, trainer in enumerate(trainers):
            for source_index, source_path in enumerate(sources):
                subcache = cache.preprocessing.create_subcache(idx)
                idx += 1

                @logger.phase(subcache)
                def _():
                    VoiceTrain._preprocess(subcache, trainer, source_path)

                train_samples = subcache.train_samples.read_paths()

                task, model = trainer.create_train_task_and_reference(
                    train_samples,
                    VoiceTrainMetadata(original_samples_path=source_path)
                )
                tasks.append(task)
                models.append(model)

        @logger.phase(cache.training)
        def _():
            unit = BrainBoxUnit()
            unit.run(cache.training, tasks)

        cache.write_result(models)
















