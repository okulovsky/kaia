import os
import pickle
from pathlib import Path

from foundation_kaia.brainbox_utils import UniqueModelStorage
from foundation_kaia.marshalling import FileLikeHandler
from interface import IZonos, FileLike

SPEAKERS_DIR = Path('/resources/speakers')
TEMP_DIR = Path('/tmp')


class ZonosService(IZonos):
    def __init__(self, storage: UniqueModelStorage):
        self.storage = storage
        self.loaded_speakers = dict()

    def train(self, speaker: str, sample: FileLike) -> None:
        tmp_file = TEMP_DIR / 'temp_train.wav'
        FileLikeHandler.write(sample, tmp_file)
        try:
            model = self.storage.get_model_data(None).model
            speaker_model = model.train(tmp_file)
        finally:
            if tmp_file.is_file():
                os.unlink(tmp_file)
        SPEAKERS_DIR.mkdir(parents=True, exist_ok=True)
        with open(SPEAKERS_DIR / speaker, 'wb') as file:
            pickle.dump(speaker_model, file)
        self.loaded_speakers[speaker] = speaker_model

    def voiceover(self,
                  text: str,
                  speaker: str,
                  language: str = 'en-us',
                  emotion: list[float] | None = None,
                  speaking_rate: float | None = None,
                  ) -> FileLike:
        if speaker not in self.loaded_speakers:
            speaker_path = SPEAKERS_DIR / speaker
            if not speaker_path.is_file():
                raise ValueError(f"Speaker {speaker} was not trained")
            with open(speaker_path, 'rb') as stream:
                self.loaded_speakers[speaker] = pickle.load(stream)
        output_file = TEMP_DIR / 'output.wav'
        model = self.storage.get_model_data(None).model
        model.voiceover(text, self.loaded_speakers[speaker], language, output_file, emotion, speaking_rate)
        with open(output_file, 'rb') as f:
            return f.read()
