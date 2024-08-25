from .settings import OpenTTSSettings
from ..arch import RemotePublicImageInstaller, DockerService, BrainBoxServiceRunner
from ..arch.utils import check_if_its_sound
from unittest import TestCase
from kaia.brainbox.deciders.open_tts.api import OpenTTS
from ...core import BrainBoxApi, BrainBoxTask, File, IntegrationTestResult


class OpenTTSInstaller(RemotePublicImageInstaller):
    def __init__(self, settings: OpenTTSSettings):
        self.settings = settings

        service = DockerService(
            self,
            settings.port,
            settings.startup_time_in_seconds,
            BrainBoxServiceRunner(
                publish_ports={self.settings.port: 5500},
                mount_data_folder=False,
            )
        )
        super().__init__('synesthesiam/opentts:en', 'open-tts', service)

    def create_api(self) -> OpenTTS:
        return OpenTTS(f'{self.ip_address}:{self.settings.port}')

    def _brainbox_self_test_internal(self, api: BrainBoxApi, tc: TestCase):
        text = IntegrationTestResult.VOICEOVER_SAMPLE
        yield IntegrationTestResult(0,None,text)
        task = BrainBoxTask.call(OpenTTS)(text=text)
        result = api.execute(task)
        tc.assertIsInstance(result, File)
        result = api.pull_content(result)
        check_if_its_sound(result, tc)
        yield IntegrationTestResult(0, None, result)








