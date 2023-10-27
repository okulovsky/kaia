from ...infra import Loc
from dataclasses import dataclass

@dataclass
class TortoiseTTSSettingsClass:
    environment = 'tortoise-tts'
    tortoise_tts_path = Loc.root_folder.parent / 'tortoise-tts'
    port = 8091
    test_voice = 'test_voice'


    @property
    def python_path(self):
        return Loc.get_python_by_env(self.environment)


    def get_voice_path(self, voice: str):
        return self.tortoise_tts_path/'tortoise/voices'/voice

@dataclass
class Automatic1111Settings:
    environment = 'automatic1111'
    automatic1111_path = Loc.root_folder.parent / 'stable-diffusion-webui'
    port = 7860
    @property
    def python_path(self):
        return Loc.get_python_by_env(self.environment)


@dataclass
class OobaboogaSettings:
    environment = 'oobabooga'
    oobabooga_path = Loc.root_folder.parent/'text-generation-webui'
    exec_path = Loc.root_folder.parent/'text-generation-webui'/('start_windows.bat' if Loc.is_windows else 'start_linux.sh')
    port = 7860
    api_port = 5000
    model_name = '4bit_WizardLM-13B-Uncensored-4bit-128g'




@dataclass
class BrainBoxSettings:
    tortoise_tts = TortoiseTTSSettingsClass()
    automatic1111 = Automatic1111Settings()
    oobabooga = OobaboogaSettings()
    file_cache_path = Loc.temp_folder / 'brainbox_cache'
    brainbox_database = Loc.temp_folder/'queue'
    brain_box_web_port = 8090



