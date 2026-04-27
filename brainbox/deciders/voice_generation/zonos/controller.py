from typing import Iterable
from ....framework import (
    RunConfiguration, SelfTestCase, BrainboxImageBuilder, IImageBuilder, DockerMarshallingController,
    BrainBoxApi, BrainBoxTask, File
)
from ...common import VOICEOVER_TEXT
from .settings import ZonosSettings
from pathlib import Path
from .app.model import ZonosInstaller
from foundation_kaia.brainbox_utils import Installer


class ZonosController(
    DockerMarshallingController[ZonosSettings],
):
    def get_image_builder(self) -> IImageBuilder | None:
        return BrainboxImageBuilder(
            Path(__file__).parent,
            '3.11.11',
            ('espeak-ng', 'ffmpeg'),
            BrainboxImageBuilder.Repository(
                'https://github.com/Zyphra/Zonos',
                'bc40d98e1e1ab54fc65c483be127a90e3c7c0645',
            ),
            dependencies=(
                BrainboxImageBuilder.PytorchDependencies('2.7.1', 'cu128', True),
                BrainboxImageBuilder.RequirementsLockTxt(True),
                BrainboxImageBuilder.KaiaFoundationDependencies()
            ),
            keep_dockerfile=True
        )

    def get_installer(self) -> Installer | None:
        return ZonosInstaller(self.resource_folder())

    def get_service_run_configuration(self, parameter: str | None) -> RunConfiguration:
        if parameter is not None:
            raise ValueError(f"`parameter` must be None for {self.get_name()}")
        return RunConfiguration(
            publish_ports={self.connection_settings.port: 8080},
        )

    def get_notebook_configuration(self) -> RunConfiguration | None:
        return self.get_service_run_configuration(None).as_notebook_service()

    def get_default_settings(self):
        return ZonosSettings()

    def create_api(self):
        from .api import ZonosApi
        return ZonosApi()

    def self_test_cases(self) -> Iterable[SelfTestCase]:
        from .api import Zonos
        speaker_sample = File.read(Path(__file__).parent / 'app/lina.mp3')
        yield SelfTestCase(Zonos.new_task().train('test_speaker', speaker_sample), None)
        yield SelfTestCase(Zonos.new_task().voiceover(VOICEOVER_TEXT, 'test_speaker'), SelfTestCase.assertFileIsSound())
        yield SelfTestCase(Zonos.new_task().voiceover(VOICEOVER_TEXT, 'test_speaker', speaking_rate=10), SelfTestCase.assertFileIsSound())
        yield SelfTestCase(Zonos.new_task().voiceover(VOICEOVER_TEXT, 'test_speaker', speaking_rate=20), SelfTestCase.assertFileIsSound())
        yield SelfTestCase(Zonos.new_task().voiceover(VOICEOVER_TEXT, 'test_speaker', emotion=Zonos.Emotions.Happiness), SelfTestCase.assertFileIsSound())
