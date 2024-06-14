import os
from dataclasses import dataclass
from .....infra import Loc
from pathlib import Path
import shutil

@dataclass
class ModelInstallationSettings:
    model_name: str
    mode: str = 'simple'
    test_dub: bool = True
    test_voice_clone: bool = False


@dataclass
class CoquiTTSSettings:
    address: str = '127.0.0.1'
    port: int = 11001
    resource_folder: Path = Loc.deciders_resources_folder/'coqui_tts'
    image_name: str = 'coqui-tts'
    use_gpu: bool = True
    builtin_models_to_download = (
        ModelInstallationSettings('tts_models/multilingual/multi-dataset/your_tts'),
        ModelInstallationSettings('tts_models/en/vctk/vits'),
        ModelInstallationSettings('tts_models/multilingual/multi-dataset/xtts_v2', mode='say_yes',test_dub=False, test_voice_clone=True),
    )


    def get_voice_path(self, voice: None|str):
        path = self.resource_folder/'voices'
        if voice is not None:
            path/=(voice+'.wav')
        return path

    def export_model_from_training(
            self,
            source_model_file_path: Path,
            model_name: str):
        target_model_file_path = self.resource_folder/f'custom/{model_name}.pth'
        os.makedirs(target_model_file_path.parent, exist_ok=True)
        shutil.copy(source_model_file_path, target_model_file_path)
        shutil.copy(source_model_file_path.parent / 'config.json', str(target_model_file_path) + '.json')
        shutil.copy(source_model_file_path.parent.parent.parent / 'data/speakers.pth', str(target_model_file_path) + '.speakers.pth')
        return f'custom_models/{model_name}.pth'



