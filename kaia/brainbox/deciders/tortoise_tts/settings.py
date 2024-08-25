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
    startup_time_in_seconds: int = 120


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




