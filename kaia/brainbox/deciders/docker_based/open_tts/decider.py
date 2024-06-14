from typing import *
from ....core import IDecider, IInstallable
from .installer import OpenTTSInstaller
from .settings import OpenTTSSettings
from uuid import uuid4

class OpenTTS(IDecider, IInstallable):
    def __init__(self, settings: OpenTTSSettings):
        self.settings = settings

    def get_installer(self) -> OpenTTSInstaller:
        return OpenTTSInstaller(self.settings)

    def warmup(self, parameters: str):
        self.get_installer().server_endpoint.run()


    def cooldown(self, parameters: str):
        self.get_installer().server_endpoint.kill()

    def __call__(self,
                 text: str,
                 voice: str = 'coqui-tts:en_vctk',
                 lang: str = 'en',
                 speakerId: Optional[str] = 'p256'):
        content = self.get_installer().create_api().call(text = text, voice = voice, lang = lang, speakerId=speakerId)
        fname = f'{uuid4()}.wav'
        with open(self.file_cache/fname, 'wb') as file:
            file.write(content)
        return [fname]