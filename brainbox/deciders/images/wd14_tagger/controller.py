import os
from typing import Iterable
from foundation_kaia.brainbox_utils import Installer
from ....framework import (
    File, RunConfiguration, SelfTestCase, BrainboxImageBuilder, IImageBuilder,
    DockerMarshallingController, BrainBoxApi, BrainBoxTask,
)
from .settings import WD14TaggerSettings
from pathlib import Path
from .app.model import WD14TaggerInstaller


class WD14TaggerController(DockerMarshallingController[WD14TaggerSettings]):
    def get_image_builder(self) -> IImageBuilder | None:
        return BrainboxImageBuilder(
            Path(__file__).parent,
            '3.11.11',
            ('ffmpeg', 'libsm6', 'libxext6'),
            BrainboxImageBuilder.Repository(
                "https://github.com/corkborg/wd14-tagger-standalone",
                "f1114c877ed6d1b1311f7e485ec0466d5064eb0c",
            ),
            allow_arm64=True,
            dependencies=(
                BrainboxImageBuilder.RequirementsLockTxt(),
                BrainboxImageBuilder.KaiaFoundationDependencies(),
            )
        )

    def get_service_run_configuration(self, parameter: str | None) -> RunConfiguration:
        if parameter is not None:
            raise ValueError(f"`parameter` must be None for {self.get_name()}")
        config = RunConfiguration(
            publish_ports={self.connection_settings.port: 8080},
        )
        if self.settings.cpu_share is not None:
            config.custom_flags = [f'--cpus={self.settings.cpu_share * os.cpu_count()}']
        return config

    def get_installer(self) -> Installer | None:
        return WD14TaggerInstaller(self.resource_folder())

    def get_default_settings(self):
        return WD14TaggerSettings()

    def create_api(self):
        from .api import WD14TaggerApi
        return WD14TaggerApi()

    def self_test_cases(self) -> Iterable[SelfTestCase]:
        from .api import WD14Tagger
        file = File.read(Path(__file__).parent / 'image.png')
        model = WD14TaggerSettings.models_to_install[0]
        yield SelfTestCase(WD14Tagger.new_task().interrogate(image=file, model=model), None)
        yield SelfTestCase(WD14Tagger.new_task().tags(model=model, count=10), None)
