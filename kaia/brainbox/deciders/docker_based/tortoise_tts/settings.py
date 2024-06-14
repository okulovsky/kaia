from typing import *
from dataclasses import dataclass
from kaia.infra import Loc
from pathlib import Path
import shutil

import os
import subprocess

@dataclass
class TortoiseTTSSettings:
    address: str = '127.0.0.1'
    image_name: str = 'tortoise-tts'
    resources_folder = Loc.deciders_resources_folder/'tortoise-tts'
    outputs_folder = Loc.deciders_resources_folder/'tortoise-tts/outputs'
    port = 11003
    test_voice = 'test_voice'
    debug: bool = False
    wait_time_in_seconds: int = 10


    def get_voice_path(self, voice: None|str = None):
        result = self.resources_folder/'voices'
        if voice is not None:
            result /= voice
        return result

    @property
    def hf_models_folder(self):
        return self.resources_folder/'models/hf'

    @property
    def tortoise_models_folder(self):
        return self.resources_folder / 'models/tortoise'


    def export_voice_for_tortoise(self, voice: str, files: Union[Path, Iterable[Path]]):
        if voice is None:
            raise ValueError("Voice cannot be None")

        if isinstance(files, Path):
            from yo_fluq_ds import Query
            files = Query.folder(files).to_list()

        tortoise_folder = self.get_voice_path(voice)
        shutil.rmtree(tortoise_folder, ignore_errors=True)
        os.makedirs(tortoise_folder)
        for file in files:
            tortoise_file = tortoise_folder / (file.name + '.wav')
            subprocess.call(['ffmpeg', '-i', file, '-ar', '22050', tortoise_file, '-y'])


