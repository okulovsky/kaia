import shutil

from .settings import RhasspySettings
from ..docker_based import DockerBasedInstaller, DockerBasedInstallerEndpoint
from .....infra.deployment import FakeContainerBuilder, DockerRun, ExistingRemoteContainerPusher
from unittest import TestCase
import requests
from pathlib import Path



class RhasspyInstaller(DockerBasedInstaller):
    def __init__(self, settings: RhasspySettings):
        self.settings = settings
        container_name = 'rhasspy/rhasspy'
        container_builder = FakeContainerBuilder(container_name)
        pusher = ExistingRemoteContainerPusher(container_name)
        self.server_endpoint = DockerBasedInstallerEndpoint(self, self._get_server_config(), 30, self.settings.port, self.settings.address)
        super().__init__(container_builder, pusher)

    def _get_server_config(self):
        folder = str(self.settings.folder).replace("\\", "/")
        additional_arguments = [
            '-d', '-p', f'{self.settings.port}:{self.settings.port}',
            '--name', 'rhasspy',
            '--restart', 'unless-stopped',
            '-v', f'{folder}:/profiles',
            '-v', '/etc/localtime:/etc/localtime:ro'
        ]
        if self.settings.propagate_sound_device:
            additional_arguments.extend(['--device', '/dev/snd:/dev/snd'])

        command_line_arguments = [
            '--user-profiles', '/profiles',
            '--profile', 'en'
        ]

        docker_run = DockerRun(
            additional_arguments=additional_arguments,
            command_line_arguments=command_line_arguments
        )
        return docker_run


    def install(self, build: bool = True):
        self.build()
        self.server_endpoint.run()
        self.server_endpoint.kill()
        self.executor.upload_file(self.settings.profile, str(self.settings.folder/'en/profile.json'))
        self.server_endpoint.run()
        requests.post(f'http://{self.settings.address}:{self.settings.port}/api/download-profile')

    def uninstall(self):
        super().uninstall()
        if self.settings.folder.is_dir():
            shutil.rmtree(self.settings.folder)

    def create_api(self):
        from kaia.avatar.dub.core import RhasspyAPI
        return RhasspyAPI(f'{self.settings.address}:{self.settings.port}')

    def self_test(self, tc: TestCase):
        from kaia.avatar.dub.core import Template
        from kaia.avatar.dub.languages.en import CardinalDub

        intents = [
            Template('Set the timer for {minutes} minutes', minutes=CardinalDub(1, 10)).with_name('timer'),
            Template('What time is it?').with_name('time')
        ]
        api = self.create_api()
        api.setup_intents(intents)
        api.train()
        result = api.recognize(Path(__file__).parent/'files/timer.wav')
        tc.assertEqual('timer', result.template.name)
        tc.assertDictEqual(dict(minutes=5), result.value)

    def get_service_endpoint(self) -> DockerBasedInstallerEndpoint:
        return self.server_endpoint



