from pathlib import Path

from brainbox import BrainBox
from .voice_train import VoiceTrain, VoiceTrainMetadata, VoiceModel
from .voice_inference import VoiceInference
from dataclasses import dataclass
from yo_fluq import FileIO
from hashlib import md5
from brainbox.deciders import Chatterbox
import subprocess
from copy import copy


@dataclass
class ChatterboxModel(VoiceModel):
    model_name: str
    model_source: str


class ChatterboxTrain(VoiceTrain):
    def create_train_task_and_reference(
            self,
            samples: list[Path],
            metadata: VoiceTrainMetadata|None = None) -> tuple[BrainBox.ITask, VoiceModel]:
        if len(samples) != 1:
            raise ValueError("Chatterbox requires a single file as a sample.")

        train_file = samples[0]

        if metadata is None:
            metadata = VoiceTrainMetadata()

        model_name = metadata.model_name
        if model_name is None:
            data = FileIO.read_bytes(train_file)
            model_name = md5(data).hexdigest()[:24]

        model = ChatterboxModel(
            model_name,
            str(metadata.original_samples_path)
        )

        task = BrainBox.Task.call(Chatterbox).train(model_name, train_file)
        return task, model

    def recode_in_proper_format(self, file: Path, folder: Path):
        target_path = folder/(file.name.split('.')[0]+'.wav')
        subprocess.call([
            'ffmpeg',
            '-i',
            str(file),
            str(target_path)
        ])
        if not target_path.is_file():
            raise ValueError(f"Conversion failed on file {file}.")

    def requires_train_single_file_with_extension(self) -> str | None:
        return 'wav'

@dataclass
class ChatterboxInference(VoiceInference):
    language: str
    cfg_weight: float = 0.5
    exaggeration: float = 0.5


    def create_task(self, model: ChatterboxModel, text: str) -> BrainBox.ITask:
        return BrainBox.Task.call(Chatterbox).voiceover(text, model.model_name, self.language, self.exaggeration, self.cfg_weight)




