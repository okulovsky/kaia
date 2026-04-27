from typing import Iterable
from foundation_kaia.brainbox_utils import Installer
from ....framework import (
    File, RunConfiguration, SelfTestCase, BrainboxImageBuilder, IImageBuilder,
    DockerMarshallingController, BrainBoxApi, BrainBoxTask,
)
from .settings import InsightFaceSettings
from pathlib import Path
from .app.model import InsightFaceInstaller


class InsightFaceController(DockerMarshallingController[InsightFaceSettings]):
    def get_image_builder(self) -> IImageBuilder | None:
        return BrainboxImageBuilder(
            Path(__file__).parent,
            '3.11.11',
            allow_arm64=True,
            dependencies=(
                BrainboxImageBuilder.CustomDependencies(('numpy==2.4.2','cython==3.2.4')),
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
        return InsightFaceInstaller(self.resource_folder())

    def get_default_settings(self):
        return InsightFaceSettings()

    def create_api(self):
        from .api import InsightFaceApi
        return InsightFaceApi()

    def self_test_cases(self) -> Iterable[SelfTestCase]:
        from .api import InsightFace
        file = File.read(Path(__file__).parent / 'files/image.png')
        yield SelfTestCase(
            InsightFace.new_task().analyze(image=file),
            lambda result, api, tc: tc.assertEqual(5, len(result))
        )
