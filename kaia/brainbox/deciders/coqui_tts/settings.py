import os
from dataclasses import dataclass
from kaia.infra import Loc
from pathlib import Path
import shutil

@dataclass
class ModelInstallationSettings:
    model_name: str
    mode: str = 'simple'
    test_dub: bool = True
    test_voice_clone: bool = False

    @property
    def due_folder_name(self):
        return self.model_name.replace('/','--')


@dataclass
class CoquiTTSSettings:
    address: str = '127.0.0.1'
    port: int = 11001
    startup_time_in_seconds = 20
    builtin_models_to_download = (
        ModelInstallationSettings('tts_models/multilingual/multi-dataset/your_tts'),
        ModelInstallationSettings('tts_models/en/vctk/vits'),
        ModelInstallationSettings('tts_models/multilingual/multi-dataset/xtts_v2', mode='say_yes',test_dub=False, test_voice_clone=True),
    )
    autoload_model: str|None = None




