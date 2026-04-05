from typing import Iterable
from foundation_kaia.brainbox_utils import Installer
from ....framework import (
    File, RunConfiguration, SelfTestCase, BrainboxImageBuilder, IImageBuilder,
    DockerMarshallingController, BrainBoxApi, BrainBoxTask,
)
from ...common import VOICEOVER_TEXT
from .settings import ChatterboxSettings
from pathlib import Path
from .app.model import ChatterboxInstaller


class ChatterboxController(DockerMarshallingController[ChatterboxSettings]):
    def get_image_builder(self) -> IImageBuilder | None:
        return BrainboxImageBuilder(
            Path(__file__).parent,
            '3.11.11',
            allow_arm64=True,
            dependencies=(
                BrainboxImageBuilder.PytorchDependencies(
                    '2.7.0', 'cu128', True
                ),
                BrainboxImageBuilder.CustomDependencies(
                    ('numpy==1.25.2',)
                ),
                BrainboxImageBuilder.RequirementsLockTxt(),
                BrainboxImageBuilder.KaiaFoundationDependencies()
            ),
            keep_dockerfile=True,
        )

    def get_installer(self) -> Installer | None:
        return ChatterboxInstaller(self.resource_folder())

    def get_service_run_configuration(self, parameter: str | None) -> RunConfiguration:
        if parameter is not None:
            raise ValueError(f"`parameter` must be None for {self.get_name()}")
        return RunConfiguration(
            publish_ports={self.connection_settings.port: 8080},
            mount_resource_folders={
                'pretrained': '/home/app/.cache/huggingface',
                'voices': '/voices',
                'speakers': '/speakers',
                'file_cache': '/file_cache',
            },
            dont_rm=False
        )

    def get_default_settings(self):
        return ChatterboxSettings()

    def create_api(self):
        from .api import ChatterboxApi
        return ChatterboxApi()

    def self_test_cases(self) -> Iterable[SelfTestCase]:
        from .api import Chatterbox
        speaker_sample = File.read(Path(__file__).parent / 'research/yc.wav')
        yield SelfTestCase(Chatterbox.new_task().train('test_speaker', speaker_sample), None)
        yield SelfTestCase(
            Chatterbox.new_task().voiceover(VOICEOVER_TEXT, 'test_speaker'),
            SelfTestCase.assertFileIsSound()
        )
