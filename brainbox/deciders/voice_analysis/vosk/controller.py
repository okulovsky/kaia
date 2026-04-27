from typing import Iterable
from foundation_kaia.brainbox_utils import Installer
from ....framework import (
    File, RunConfiguration, SelfTestCase, BrainboxImageBuilder, IImageBuilder,
    DockerMarshallingController, BrainBoxApi, BrainBoxTask,
)
from .settings import VoskSettings
from pathlib import Path
from .app.model import VoskInstaller


class VoskController(DockerMarshallingController[VoskSettings]):
    def get_image_builder(self) -> IImageBuilder | None:
        return BrainboxImageBuilder(
            Path(__file__).parent,
            '3.11.11',
            ('ffmpeg',),
            allow_arm64=True,
            dependencies=(
                BrainboxImageBuilder.RequirementsLockTxt(),
                BrainboxImageBuilder.KaiaFoundationDependencies()
            )
        )

    def get_service_run_configuration(self, parameter: str | None) -> RunConfiguration:
        if parameter is not None:
            raise ValueError(f"`parameter` must be None for {self.get_name()}")
        return RunConfiguration(
            publish_ports={self.connection_settings.port: 8080},
        )

    def get_installer(self) -> Installer | None:
        return VoskInstaller(self.resource_folder())

    def get_default_settings(self):
        return VoskSettings()

    def create_api(self):
        from .api import VoskApi
        return VoskApi()

    def self_test_cases(self) -> Iterable[SelfTestCase]:
        from .api import Vosk
        file = File.read(Path(__file__).parent / 'files/test_voice.wav')
        def check_transcribe(result, api, tc):
            tc.assertEqual(1, len(result))
            tc.assertEqual('one little spark and before you know it the whole world is burning', result[0]['text'])
            tc.assertEqual(13, len(result[0]['result']))
            tc.assertIn('conf', result[0]['result'][0])
            tc.assertIn('start', result[0]['result'][0])
            tc.assertIn('end', result[0]['result'][0])
            tc.assertIn('word', result[0]['result'][0])
        yield SelfTestCase(Vosk.new_task().transcribe(file, 'en'), check_transcribe)
        yield SelfTestCase(Vosk.new_task().transcribe_to_array(file, 'en'), None)
