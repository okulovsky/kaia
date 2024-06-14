from .settings import OpenTTSSettings
from ..docker_based import DockerBasedInstaller, DockerBasedInstallerEndpoint
from .....infra.deployment import FakeContainerBuilder, DockerRun, ExistingRemoteContainerPusher
from unittest import TestCase
from kaia.brainbox.deciders.api.open_tts import OpenTTSApi
from ..utils import check_if_its_sound


class OpenTTSInstaller(DockerBasedInstaller):
    def __init__(self, settings: OpenTTSSettings):
        self.settings = settings
        container_builder = FakeContainerBuilder(settings.image_name)
        pusher = ExistingRemoteContainerPusher(settings.image_name)

        config = DockerRun(
            mapped_ports={5500:self.settings.port},
            additional_arguments=['--name', self.settings.name, '-d', '-it','--rm']
        )

        self.server_endpoint = DockerBasedInstallerEndpoint(self, config, self.settings.waiting_time, self.settings.port)
        super().__init__(container_builder, pusher)

    def install(self):
        self.build()
        self.server_endpoint.run()
        self.server_endpoint.kill()

    def create_api(self):
        return OpenTTSApi(f'{self.settings.address}:{self.settings.port}')

    def self_test(self, tc: TestCase):
        self.server_endpoint.run()
        api = self.create_api()
        result = api.call(text='Hello OpenTTS')
        check_if_its_sound(result, tc)
        self.server_endpoint.kill()

    def get_service_endpoint(self) -> DockerBasedInstallerEndpoint:
        return self.server_endpoint





