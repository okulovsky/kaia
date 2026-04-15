from pathlib import Path

from brainbox import BrainBox
from .voice_train import VoiceTrain, VoiceTrainMetadata, VoiceModel
from .voice_inference import VoiceInference
from dataclasses import dataclass
from hashlib import md5
from brainbox.deciders import CosyVoice


@dataclass
class CosyVoiceModel(VoiceModel):
    model_name: str
    model_source: str
    model_source_text: str


class CosyVoiceTrain(VoiceTrain):
    def create_train_task_and_reference(
            self,
            samples: list[Path],
            samples_metadata: list[dict],
            metadata: VoiceTrainMetadata|None = None
    ) -> tuple[BrainBox.Task, VoiceModel]:
        if len(samples) != 1:
            raise ValueError(f"Cosyvoice requires a single file as a sample, but the sample list was of length {len(samples)}.\n{samples}")

        train_file = samples[0]
        text = samples_metadata[0]['transcription']

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

        task = CosyVoice.new_task().train(model_name, text, train_file)
        return task, model

    def get_metadata_extensions(self) -> tuple[str,...]:
        return ('transcription',)

    def aggregate_metadata(self, data: list[dict]) -> dict:
        return dict(transcription=' '.join(d['transcription'].strip() for d in data))

    def requires_train_single_file_with_extension(self) -> str | None:
        return 'wav'

@dataclass
class CosyVoiceInference(VoiceInference):
    translanguage: bool

    def create_task(self, model: CosyVoiceModel, text: str) -> BrainBox.Task:
        if self.translanguage:
            return CosyVoice.new_task().voice_to_text_translingual(model.model_name, text)
        else:
            return CosyVoice.new_task().voice_to_text(model.model_name, text)






