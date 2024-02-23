from typing import *
from dataclasses import dataclass
from ...core import IDecider
from ....infra import Loc

@dataclass
class OpenVoiceSettings:
    location = Loc.root_folder.parent/'openvoice'
    environment = 'openvoice'

    @property
    def python_path(self):
        return Loc.get_python_by_env(self.environment)

    def get_voice_file(self, voice: Optional[str] = None):
        path = self.location/'voices'
        if voice is not None:
            path/=voice+".wav"
        return path


class OpenVoice(IDecider):
    def __init__(self, settings: OpenVoiceSettings):
        self.settings = settings

    def warmup(self, parameters: str):
        pass

    def cooldown(self, parameters: str):
        pass

    def __call__(self):
        pass