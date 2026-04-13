import os
from uuid import uuid4

from interface import IWhisper
from foundation_kaia.brainbox_utils import SingleModelStorage
from foundation_kaia.marshalling import FileLike, FileLikeHandler, JSON


class WhisperService(IWhisper):
    def __init__(self, storage: SingleModelStorage):
        self.storage = storage

    def transcribe(
        self,
        file: FileLike,
        model: str | None = None,
        initial_prompt: str | None = None,
        options: dict[str, JSON] | None = None,
    ) -> dict:
        fname = f'/resources/input_{uuid4()}.wav'
        try:
            FileLikeHandler.write(file, fname)
            loaded_model = self.storage.get_model(model)
            kwargs = options or {}
            if initial_prompt is not None:
                kwargs['initial_prompt'] = initial_prompt
            result = loaded_model.transcribe(fname, **kwargs)
            return result
        finally:
            if os.path.exists(fname):
                os.unlink(fname)


    def transcribe_text(
        self,
        file: FileLike,
        model: str | None = None,
        initial_prompt: str | None = None,
        options: dict | None = None,
    ) -> str:
        result = self.transcribe(file, model, initial_prompt, options)
        return result.get('text', '').strip()