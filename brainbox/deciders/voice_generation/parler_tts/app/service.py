import os
import uuid
from pathlib import Path

from foundation_kaia.brainbox_utils import SingleModelStorage
from foundation_kaia.marshalling import FileLike
from interface import IParlerTts
from processing import Model

SPEAKERS_DIR = Path('/resources/speakers')
TEMP_DIR = Path('/tmp')


class ParlerTtsService(IParlerTts):
    def __init__(self, storage: SingleModelStorage):
        self.storage = storage

    def train(self, speaker: str, description: str) -> None:
        SPEAKERS_DIR.mkdir(parents=True, exist_ok=True)
        (SPEAKERS_DIR / f'{speaker}.txt').write_text(description, encoding='utf-8')

    def get_speakers(self) -> dict[str, str]:
        if not SPEAKERS_DIR.is_dir():
            return {}
        return {
            file.stem: file.read_text(encoding='utf-8')
            for file in sorted(SPEAKERS_DIR.glob('*.txt'))
        }

    def voiceover(
        self,
        text: str,
        speaker: str,
        model: str | None = None,
        temperature: float = 1.0,
        seed: int | None = None,
    ) -> FileLike:
        speaker_file = SPEAKERS_DIR / f'{speaker}.txt'
        if not speaker_file.is_file():
            raise ValueError(f"Speaker {speaker} was not trained")
        return self.voiceover_with_description(
            text,
            speaker_file.read_text(encoding='utf-8'),
            model,
            temperature,
            seed
        )

    def voiceover_with_description(
        self,
        text: str,
        description: str,
        model: str | None = None,
        temperature: float = 1.0,
        seed: int | None = None,
    ) -> FileLike:
        output_file = TEMP_DIR / f'{uuid.uuid4()}.wav'
        try:
            loaded_model: Model = self.storage.get_model(model)
            loaded_model.voiceover(text, description, output_file, temperature, seed)
            return output_file.read_bytes()
        finally:
            if output_file.is_file():
                os.unlink(output_file)
