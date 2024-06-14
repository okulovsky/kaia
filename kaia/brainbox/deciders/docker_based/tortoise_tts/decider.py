from .settings import TortoiseTTSSettings
from .installer import TortoiseTTSInstaller
from ....core import IDecider, IInstallable
import shutil


class TortoiseTTS(IDecider, IInstallable):
    def __init__(self, settings: TortoiseTTSSettings):
        self.settings = settings


    def warmup(self, parameters: str):
        self.get_installer().server_endpoint.run()

    def cooldown(self, parameters: str):
        self.get_installer().server_endpoint.kill()


    def get_installer(self) -> TortoiseTTSInstaller:
        return TortoiseTTSInstaller(self.settings)


    def __call__(self, voice: str, text: str, count=3):
        files = self.get_installer().create_api().dub_and_return_filenames(text, voice, count)
        if self.settings.outputs_folder != self.file_cache:
            for file in files:
                shutil.move(self.settings.outputs_folder/file, self.file_cache/file)
        return files

