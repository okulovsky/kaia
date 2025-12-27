from pathlib import Path

from brainbox import BrainBox
from .voice_train import VoiceTrain, VoiceTrainMetadata, VoiceModel
from .voice_inference import VoiceInference
from dataclasses import dataclass
from yo_fluq import FileIO
from hashlib import md5
from brainbox.deciders import CoquiTTS, Empty
import subprocess
from copy import copy


@dataclass
class XTTSModel(VoiceModel):
    model_name: str
    model_source: str


class XTTSTrain(VoiceTrain):
    def create_train_task_and_reference(
            self,
            samples: list[Path],
            metadata: VoiceTrainMetadata|None = None) -> tuple[BrainBox.ITask, VoiceModel]:

        if metadata is None:
            metadata = VoiceTrainMetadata()

        model_name = metadata.model_name

        if model_name is None:
            model_name = self.compute_hash(samples)

        model = XTTSModel(
            model_name,
            str(metadata.original_samples_path)
        )

        task = BrainBox.ExtendedTask(
            BrainBox.Task.call(Empty)(),
            prerequisite=CoquiTTS.upload_voice(
                model_name,
                *samples
            )
        )
        return task, model

    def requires_train_single_file_with_extension(self) -> str | None:
        return None

@dataclass
class XTTSInference(VoiceInference):
    language: str = 'en'

    def create_task(self, model: XTTSModel, text: str) -> BrainBox.ITask:
        return BrainBox.Task.call(CoquiTTS).voice_clone(
            text,
            model='tts_models/multilingual/multi-dataset/xtts_v2',
            voice=model.model_name,
            language=self.language
        )




