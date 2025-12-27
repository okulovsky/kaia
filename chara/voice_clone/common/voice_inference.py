from .voice_train import VoiceModel
from chara.common import BrainBoxUnit, BrainBoxCache, ICache, FileCache, logger
from chara.common.tools import Wav
from abc import ABC, abstractmethod
from typing import Iterable, Any
from brainbox import BrainBox
from copy import copy
from pathlib import Path
from dataclasses import dataclass

class VoiceInferenceCache(ICache[Wav.List]):
    def __init__(self, working_folder: Path|None = None):
        super().__init__(working_folder)
        self.metadata = FileCache[list[dict]]()
        self.voiceover = BrainBoxCache[Any,str]()


@dataclass
class InferenceCase:
    inference_index: int
    inference: 'VoiceInference'
    model_index: int
    model: VoiceModel
    text: str


class VoiceInference(ABC):
    Cache = VoiceInferenceCache

    @abstractmethod
    def create_task(self, model: VoiceModel, text: str) -> BrainBox.ITask:
        pass

    def get_metadata(self) -> dict:
        return copy(self.__dict__)


    @staticmethod
    def _create_task(case: InferenceCase) -> BrainBox.ITask:
        return case.inference.create_task(case.model, case.text)


    @staticmethod
    def pipeline(
            cache: VoiceInferenceCache,
            inferences: 'VoiceInference|Iterable[VoiceInference]',
            models: VoiceModel|Iterable[VoiceModel],
            texts: str|Iterable[str]
    ):
        if cache.ready:
            return

        if isinstance(models, VoiceModel):
            models = [models]
        else:
            models = list(models)

        if isinstance(texts, str):
            texts = [texts]
        else:
            texts = list(texts)

        if isinstance(inferences, VoiceInference):
            inferences = [inferences]
        else:
            inferences = list(inferences)

        cases = [
            InferenceCase(inference_index, inference, model_index, model, text)
            for inference_index, inference in enumerate(inferences)
            for model_index, model in enumerate(models)
            for text in texts
        ]

        @logger.phase(cache.metadata)
        def _():
            metadatas = []
            for case in cases:
                metadata = case.model.get_metadata()
                metadata |= case.inference.get_metadata()
                metadata['text'] = case.text
                metadata['model_index'] = case.model_index
                metadata['inference_index'] = case.inference_index
                metadata['model_class'] = type(case.model).__name__
                metadata['inference_class'] = type(case.inference).__name__
                metadatas.append(metadata)
            cache.metadata.write(metadatas)

        @logger.phase(cache.voiceover)
        def _():
            unit = BrainBoxUnit(
                VoiceInference._create_task,
                options_as_files=True
            )
            unit.run(cache.voiceover, cases)

        result = []
        en = zip(
            cache.metadata.read(),
            cache.voiceover.read_cases_and_options()
        )
        for metadata, (case, option) in en:
            wav = Wav.one(cache.voiceover.get_file_path(option))
            for key, value in metadata.items():
                wav.metadata[key] = value
            result.append(wav)

        wavs = Wav.many(result)
        cache.write_result(wavs)