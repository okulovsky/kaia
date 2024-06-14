from ....core import IDecider, IInstallable
from .settings import CoquiTTSSettings
from .installer import CoquiTTSInstaller
from uuid import uuid4


class CoquiTTS(IDecider, IInstallable):
    def __init__(self, settings: CoquiTTSSettings):
        self.settings = settings
        self.model_info = None


    def _postprocess(self, result):
        fname = f'{uuid4()}.wav'
        with open(self.file_cache/fname, 'wb') as file:
            file.write(result)
        return [fname]


    def dub(self, text, voice, language=None):
        return self._postprocess(self.get_installer().create_api().dub(self.model_info, text, voice, language))


    def voice_clone(self, text, voice, language = None):
        return self._postprocess(self.get_installer().create_api().voice_clone(self.model_info, text, voice, language))


    def warmup(self, parameters: str):
        self.get_installer().server_endpoint.run()
        if parameters.strip()!='':
            self.model_info = self.get_installer().create_api().load_model(parameters)

    def cooldown(self, parameters: str):
        self.get_installer().server_endpoint.kill()

    def get_installer(self) -> CoquiTTSInstaller:
        return CoquiTTSInstaller(self.settings)

