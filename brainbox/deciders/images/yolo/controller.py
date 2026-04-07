from typing import Iterable
from foundation_kaia.brainbox_utils import Installer
from ....framework import (
    File, RunConfiguration, SelfTestCase, BrainboxImageBuilder, IImageBuilder,
    DockerMarshallingController, BrainBoxApi, BrainBoxTask,
)
from .settings import YoloSettings, YoloModels
from pathlib import Path
from .app.model import YoloInstaller


class YoloController(DockerMarshallingController[YoloSettings]):
    def get_image_builder(self) -> IImageBuilder | None:
        return BrainboxImageBuilder(
            Path(__file__).parent,
            '3.11.11',
            ('libgl1',),
            allow_arm64=True,
            dependencies=(
                BrainboxImageBuilder.PytorchDependencies(
                    '2.7.0', 'cu128', None, '0.22.0'
                ),
                BrainboxImageBuilder.RequirementsLockTxt(),
                BrainboxImageBuilder.KaiaFoundationDependencies(),
            )
        )

    def get_service_run_configuration(self, parameter: str | None) -> RunConfiguration:
        if parameter is not None:
            raise ValueError(f"`parameter` must be None for {self.get_name()}")
        return RunConfiguration(
            publish_ports={self.connection_settings.port: 8080},
        )

    def get_installer(self) -> Installer | None:
        return YoloInstaller(self.resource_folder())

    def get_default_settings(self):
        return YoloSettings()

    def create_api(self):
        from .api import YoloApi
        return YoloApi()

    def self_test_cases(self) -> Iterable[SelfTestCase]:
        from .api import Yolo
        yield SelfTestCase(
            Yolo.new_task().analyze(
                File.read(Path(__file__).parent / 'test_anime_img.png'),
                YoloModels.yolov8_animeface,
            ),
            lambda result, api, tc: tc.assertIn('objects', result)
        )
