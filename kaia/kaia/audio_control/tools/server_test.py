from ..setup.settings import AudioControlSettings
from ..core import AudioControlServer, AudioControlAPI
from kaia.infra.app import KaiaApp
import sys

class ServerTest:
    def __init__(self, settings: AudioControlSettings):
        self.settings = settings

    def _print(self, s):
        print(s)
        sys.stdout.flush()

    def __call__(self):
        server = AudioControlServer(self.settings.create_audio_control, self.settings.port)
        app = KaiaApp()
        app.add_subproc_service(server)
        self._print('Running ACserver')
        app.run_services_only()
        api = AudioControlAPI(f'127.0.0.1:{self.settings.port}')
        self._print('Entering main cycle. Waiting for the server')
        api.wait_for_availability()
        self._print('Server is available')
        while True:
            command = api.wait_for_command()
            self._print(command)
            api.set_mode('whisper')
            command = api.wait_for_command()
            self._print(command)





