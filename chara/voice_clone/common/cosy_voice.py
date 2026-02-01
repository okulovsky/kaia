from pathlib import Path

from brainbox import BrainBox
from .voice_train import VoiceTrain, VoiceTrainMetadata, VoiceModel
from .voice_inference import VoiceInference
from dataclasses import dataclass
from yo_fluq import FileIO
from hashlib import md5
from brainbox.deciders import CosyVoice
import subprocess
from copy import copy


@dataclass
class CosyVoiceModel(VoiceModel):
    model_name: str
    model_source: str
    model_source_text: str


class CosyVoiceTrain(VoiceTrain):
    def create_train_task_and_reference(
            self,
            samples: list[Path],
            metadata: VoiceTrainMetadata|None = None) -> tuple[BrainBox.ITask, VoiceModel]:
        if len(samples) != 1:
            raise ValueError(f"Chatterbox requires a single file as a sample, but the sample list was of length {len(samples)}.")

        train_file = samples[0]
        text_file = Path(str(train_file)+".txt")

        with open(text_file, 'r') as f:
            text = f.read()

        if metadata is None:
            metadata = VoiceTrainMetadata()

        model_name = metadata.model_name
        if model_name is None:
            model_name = self.compute_hash(samples)+md5(text.encode()).hexdigest()[:12]

        model = CosyVoiceModel(
            model_name,
            str(metadata.original_samples_path),
            text
        )

        task = BrainBox.Task.call(CosyVoice).train(model_name, train_file, text)
        return task, model


    def requires_train_single_file_with_extension(self) -> str | None:
        return 'wav'

class CosyVoiceInference(VoiceInference):
    translanguage: bool

    def create_task(self, model: CosyVoiceModel, text: str) -> BrainBox.ITask:
        if self.translanguage:
            return BrainBox.Task.call(CosyVoice).voice_to_text_transligual(model.model_name, text)
        else:
            return BrainBox.Task.call(CosyVoice).voice_to_text(model.model_name, text)






