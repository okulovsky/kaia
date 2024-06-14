from ....core import IDecider, IInstallable
from .settings import WhisperSettings
from .installer import WhisperInstaller

class Whisper(IDecider, IInstallable):
    def __init__(self, settings: WhisperSettings):
        self.settings = settings
        self.model_info = None

    def transcribe(self, filename:str):
        return self.get_installer().create_api().transcribe(self.file_cache/filename)

    def transcribe_text_only(self, filename: str):
        result = self.transcribe(filename)
        return result.get('text','').strip()

    def warmup(self, parameters: str):
        self.get_installer().server_endpoint.run()
        if parameters is not None:
            self.model_info = self.get_installer().create_api().load_model(parameters)
        else:
            self.get_installer().create_api().load_model(self.settings.default_model)

    def cooldown(self, parameters: str):
        self.get_installer().server_endpoint.kill()

    def get_installer(self) -> WhisperInstaller:
        return WhisperInstaller(self.settings)

