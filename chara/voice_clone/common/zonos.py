from pathlib import Path

from brainbox import BrainBox
from .voice_train import VoiceTrain, VoiceTrainMetadata, VoiceModel
from .voice_inference import VoiceInference
from dataclasses import dataclass
from yo_fluq import FileIO
from hashlib import md5
from brainbox.deciders import Zonos
import subprocess
from copy import copy


@dataclass
class ZonosModel(VoiceModel):
    model_name: str
    model_source: str


class ZonosTrain(VoiceTrain):
    def create_train_task_and_reference(
            self,
            samples: list[Path],
            metadata: VoiceTrainMetadata|None = None) -> tuple[BrainBox.ITask, VoiceModel]:

        if metadata is None:
            metadata = VoiceTrainMetadata()

        model_name = metadata.model_name

        if model_name is None:
            model_name = self.compute_hash(samples)

        model = ZonosModel(
            model_name,
            str(metadata.original_samples_path)
        )

        task = BrainBox.Task.call(Zonos).train(model_name, samples)
        return task, model

    def requires_train_single_file_with_extension(self) -> str | None:
        return None

@dataclass
class ZonosInference(VoiceInference):
    language: str = 'en-us'
    emotion: list[float]|None = None


    def create_task(self, model: ZonosModel, text: str) -> BrainBox.ITask:
        return BrainBox.Task.call(Zonos).voiceover(text, model.model_name, self.language, self.emotion)




