from typing import *
import os

from model_file_info import ModelFileInfo
from pathlib import Path
import shutil
from threading import Thread
import time
from TTS.api import TTS
from service import Service
from utils import get_working_folder

class Sampler(Service):
    def __init__(self,
                 text: str,
                 folder: Path,
                 voices: List[str|None],
                 sleep_in_seconds: int = 60
                 ):
        super().__init__(folder, sleep_in_seconds)
        self.text = text
        self.voices = voices
        os.makedirs(self.folder.parent/'samples', exist_ok=True)

    def get_sample_name(self, voice, step):
        if voice is None:
            voice = 'NONE'
        fname = self.folder.parent/'samples'/f'sample_{voice}_{step}.wav'
        return fname


    def generate_from_model(self, model_file, step):
        tts = TTS(model_path=model_file, config_path=model_file.parent / 'config.json').to('cpu')
        for voice in self.voices:
            speaker_name = 'VCTK_'+voice if voice is not None else None
            wav = tts.synthesizer.tts(
                text=self.text,
                speaker_name=speaker_name,
                language_name="en",
                speaker_wav=None,
                reference_wav=None,
                style_wav=None,
                style_text=None,
                reference_speaker_name=None,
                split_sentences=True,
            )
            tts.synthesizer.save_wav(wav=wav,path=self.get_sample_name(voice, step),pipe_out=None)
        del tts

    def _iteration(self):
        models_folder = get_working_folder(self.folder)
        if models_folder is None:
            return

        models = ModelFileInfo.parse_folder(models_folder)
        models = [m for m in models if m.type!=ModelFileInfo.Type.Checkpoint]
        for model in models:
            should_generate = False
            for voice in self.voices:
                fname = self.get_sample_name(voice, model.step)
                if not fname.is_file():
                    should_generate = True
                    break
            if not should_generate:
                continue
            self.generate_from_model(model.path, model.step)
