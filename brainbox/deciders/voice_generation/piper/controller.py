from typing import Iterable
from ....framework import (
    RunConfiguration, SelfTestCase, BrainboxImageBuilder, IImageBuilder, DockerMarshallingController,
    BrainBoxApi, BrainBoxTask, File
)
from .settings import PiperSettings
from pathlib import Path
from ...common import VOICEOVER_TEXT
from .app.model import PiperInstaller
from foundation_kaia.brainbox_utils import Installer


class PiperController(DockerMarshallingController[PiperSettings]):
    def get_image_builder(self) -> IImageBuilder | None:
        return BrainboxImageBuilder(
            Path(__file__).parent,
            'lscr.io/linuxserver/piper:1.6.3',
            ('python3', 'python3-pip', 'wget'),
            dependencies=(
                BrainboxImageBuilder.KaiaFoundationDependencies(),
            ),
            install_requirements_as_root=True,
            allow_arm64=True
        )

    def get_installer(self) -> Installer | None:
        return PiperInstaller(self.resource_folder())

    def get_service_run_configuration(self, parameter: str | None) -> RunConfiguration:
        if parameter is not None:
            raise ValueError(f"`parameter` must be None for {self.get_name()}")
        return RunConfiguration(
            publish_ports={self.connection_settings.port: 8080},
        )

    def get_default_settings(self):
        return PiperSettings

    def create_api(self):
        from .api import PiperApi
        return PiperApi()

    def self_test_cases(self) -> Iterable[SelfTestCase]:
        from .api import Piper
        yield SelfTestCase(
            Piper.new_task().voiceover(text=VOICEOVER_TEXT, model="en"),
            SelfTestCase.assertFileIsSound()
        )
