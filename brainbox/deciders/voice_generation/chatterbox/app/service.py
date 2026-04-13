import os
import shutil
import uuid
from pathlib import Path

from interface import IChatterbox
from processing import Model
from chatterbox.mtl_tts import Conditionals
from foundation_kaia.marshalling import FileLike, FileLikeHandler


class ChatterboxService(IChatterbox):
    def __init__(self, storage):
        self.storage = storage
        self.voices_folder = Path('/voices')
        self.speakers_folder = Path('/speakers')
        self.speakers_cache = {}

    def _get_model(self) -> Model:
        return self.storage.get_model_data(None).model

    def train(self, speaker: str, file: FileLike) -> None:
        voice_folder = self.voices_folder / speaker
        shutil.rmtree(voice_folder, ignore_errors=True)
        os.makedirs(voice_folder)
        file_path = voice_folder / 'sample.wav'
        FileLikeHandler.write(file, file_path)
        model = self._get_model()
        embedding = model.compute_embedding(file_path)
        self.speakers_cache[speaker] = embedding
        embedding.save(self.speakers_folder / speaker)

    def voiceover(
        self,
        text: str,
        speaker: str,
        language: str = 'en',
        exaggeration: float = 0.5,
        cfg_weight: float = 0.5,
    ) -> FileLike:
        temp_file = Path('/file_cache') / f'{uuid.uuid4()}.wav'
        try:
            model = self._get_model()
            if speaker not in self.speakers_cache:
                speaker_file = self.speakers_folder / speaker
                if not speaker_file.is_file():
                    raise ValueError(f"Speaker {speaker} was not trained")
                self.speakers_cache[speaker] = Conditionals.load(speaker_file, model.device)
            model.voiceover(text, self.speakers_cache[speaker], language, temp_file, exaggeration, cfg_weight)
            return temp_file.read_bytes()
        finally:
            if temp_file.is_file():
                os.unlink(temp_file)
