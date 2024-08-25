from unittest import TestCase
from ..arch import DockerService, BrainBoxServiceRunner, RemotePublicImageInstaller
from .settings import RhasspySettings
from .api import Rhasspy
from ...core import BrainBoxApi, BrainBoxTask, IntegrationTestResult, File
from pathlib import Path
import requests
from kaia.dub.core import Template
from kaia.dub.languages.en import CardinalDub
import json

class RhasspyInstaller(RemotePublicImageInstaller):
    def __init__(self, settings: RhasspySettings):
        self.settings = settings

        service = DockerService(
            self,
            settings.port,
            settings.startup_timeout_in_seconds,
            BrainBoxServiceRunner(
                publish_ports={self.settings.port: 12101},
                mount_resource_folders={'profiles':'/profiles'},
                custom_flags =  ['-v', '/etc/localtime:/etc/localtime:ro'],
                command_line_arguments=['--user-profiles', '/profiles', '--profile', 'en'],
                mount_data_folder=False,
            )
        )

        super().__init__('rhasspy/rhasspy','rhasspy', service)

    def create_api(self) -> Rhasspy:
        return Rhasspy(f'{self.ip_address}:{self.settings.port}')

    def post_install(self):
        self.executor.upload_file(self.settings.profile, str(self.resource_folder('profiles','en')/'profile.json'))
        self.run_in_any_case_and_create_api()
        requests.post(f'http://{self.ip_address}:{self.settings.port}/api/download-profile')
        self.kill()
        if self.settings.custom_words is not None:
            api: Rhasspy = self.run_in_any_case_and_create_api()
            api.set_custom_words(self.settings.custom_words)
            self.kill()



    def _brainbox_self_test_internal(self, api: BrainBoxApi, tc: TestCase):

        intents = [
            Template('Set the timer for {minutes} minutes', minutes=CardinalDub(1, 10)).with_name('timer'),
            Template('What time is it?').with_name('time')
        ]
        api.execute(BrainBoxTask.call(Rhasspy).train(intents=intents))

        file = File.read(Path(__file__).parent/'files/timer.wav')
        yield IntegrationTestResult(0,None,file)

        result = api.execute(BrainBoxTask.call(Rhasspy).recognize(file=file))
        tc.assertEqual('timer', result['intent']['name'])
        tc.assertEqual('five', result['entities'][0]['raw_value'])
        js = File("response.json", json.dumps(result), File.Kind.Json)
        yield IntegrationTestResult(0, None, js)





