import os
import pickle
import uuid
from pathlib import Path
from resemblyzer import preprocess_wav, VoiceEncoder

from foundation_kaia.marshalling import FileLikeHandler
from interface import IResemblyzer, FileLike
from resemblyzer import preprocess_wav, VoiceEncoder


DATASETS_PATH = Path('/resources/datasets')
MODELS_FOLDER = Path('/resources/models')
TEMP_DIR = Path('/tmp')


class ResemblyzerService(IResemblyzer):
    def __init__(self):
        self.encoder = VoiceEncoder()

    def _get_embedding(self, file: FileLike):
        path = TEMP_DIR / str(uuid.uuid4())
        FileLikeHandler.write(file, path)
        try:
            preprocessed = preprocess_wav(path)
            return self.encoder.embed_utterance(preprocessed)
        finally:
            if path.is_file():
                os.unlink(path)

    def vector(self, file: FileLike) -> list[float]:
        embedding = self._get_embedding(file)
        return [float(e) for e in embedding]
