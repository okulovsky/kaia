import io
import os
import uuid
from pathlib import Path
import torchaudio

from interface import ICosyVoice
from foundation_kaia.brainbox_utils import SingleModelStorage
from foundation_kaia.marshalling_2 import FileLike, FileLikeHandler


class CosyVoiceService(ICosyVoice):
    def __init__(self, storage: SingleModelStorage):
        self.storage = storage

    def _to_wav_bytes(self, model, en) -> bytes:
        for content in en:
            buf = io.BytesIO()
            torchaudio.save(buf, content['tts_speech'], model.sample_rate, format="wav")
            buf.seek(0)
            return buf.read()

    def train(self, voice: str, text: str, file: FileLike, model: str|None = None) -> None:
        m = self.storage.get_model(model)
        voices_path = Path('/resources/voices')
        voices_path.mkdir(parents=True, exist_ok=True)
        voice_path = voices_path / f'{voice}.wav'
        FileLikeHandler.write(file, str(voice_path))
        m.add_zero_shot_spk(text, str(voice_path), voice)
        m.save_spkinfo()

    def voice_to_file(self, voice: str, file: FileLike, model: str|None = None) -> FileLike:
        m = self.storage.get_model(model)
        voice_path = f'/resources/voices/{voice}.wav'
        temp_path = f'/resources/temp/{uuid.uuid4()}.wav'
        os.makedirs('/resources/temp', exist_ok=True)
        FileLikeHandler.write(file, temp_path)
        result = self._to_wav_bytes(m, m.inference_vc(temp_path, voice_path, stream=False))
        if os.path.isfile(temp_path):
            os.unlink(temp_path)
        return result

    def voice_to_text(self, voice: str, text: str, model: str|None = None) -> FileLike:
        m = self.storage.get_model(model)
        return self._to_wav_bytes(m, m.inference_zero_shot(
            text,
            prompt_text='',
            prompt_wav=None,
            zero_shot_spk_id=voice
        ))

    def voice_to_text_translingual(self, voice: str, text: str, model: str|None = None) -> FileLike:
        m = self.storage.get_model(model)
        return self._to_wav_bytes(m, m.inference_cross_lingual(
            text, prompt_wav=None, zero_shot_spk_id=voice, stream=False
        ))
