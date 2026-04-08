from pathlib import Path

from brainbox import BrainBox
from .voice_train import VoiceTrain, VoiceTrainMetadata, VoiceModel
from .voice_inference import VoiceInference
from dataclasses import dataclass
from brainbox.deciders import Chatterbox


@dataclass
class ChatterboxModel(VoiceModel):
    model_name: str
    model_source: str


class ChatterboxTrain(VoiceTrain):
    def create_train_task_and_reference(
            self,
            samples: list[Path],
            samples_metadata: list[dict],
            metadata: VoiceTrainMetadata|None = None
    ) -> tuple[BrainBox.Task, VoiceModel]:
        if len(samples) != 1:
            raise ValueError(f"Chatterbox requires a single file as a sample, but the sample list was of length {len(samples)}.")

        train_file = samples[0]

        if metadata is None:
            metadata = VoiceTrainMetadata()

        model_name = metadata.model_name
        if model_name is None:
            model_name = self.compute_hash(samples)

        model = ChatterboxModel(
            model_name,
            str(metadata.original_samples_path)
        )

        task = Chatterbox.new_task().train(model_name, train_file)
        return task, model


    def requires_train_single_file_with_extension(self) -> str | None:
        return 'wav'

@dataclass
class ChatterboxInference(VoiceInference):
    language: str = 'en'
    cfg_weight: float = 0.5
    exaggeration: float = 0.5


    def create_task(self, model: ChatterboxModel, text: str) -> BrainBox.Task:
        return Chatterbox.new_task().voiceover(text, model.model_name, self.language, self.exaggeration, self.cfg_weight)




