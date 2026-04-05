from typing import Iterable
from ....framework import (
    RunConfiguration, SelfTestCase, BrainboxImageBuilder, IImageBuilder, DockerMarshallingController,
    BrainBoxApi, BrainBoxTask, File
)
from .settings import ResemblyzerSettings
from pathlib import Path


class ResemblyzerController(DockerMarshallingController[ResemblyzerSettings]):
    def get_image_builder(self) -> IImageBuilder | None:
        return BrainboxImageBuilder(
            Path(__file__).parent,
            '3.10.14',
            allow_arm64=True,
            dependencies=(
                BrainboxImageBuilder.PytorchDependencies('2.3.1', None, False),
                BrainboxImageBuilder.RequirementsLockTxt(no_deps=True),
                BrainboxImageBuilder.KaiaFoundationDependencies(),
            ),
            keep_dockerfile=True,
        )

    def get_service_run_configuration(self, parameter: str | None) -> RunConfiguration:
        if parameter is not None:
            raise ValueError(f"`parameter` must be None for {self.get_name()}")
        return RunConfiguration(
            publish_ports={self.connection_settings.port: 8080},
            dont_rm = True
        )

    def get_notebook_configuration(self) -> RunConfiguration | None:
        return self.get_service_run_configuration(None).as_notebook_service()

    def get_default_settings(self):
        return ResemblyzerSettings()

    def create_api(self):
        from .api import ResemblyzerApi
        return ResemblyzerApi()

    def self_test_cases(self) -> Iterable[SelfTestCase]:
        from .api import Resemblyzer
        file = File.read(Path(__file__).parent / 'test_voice.wav')
        yield SelfTestCase(
            Resemblyzer.new_task().vector(file),
            lambda result, api, tc: tc.assertIsInstance(result, list)
        )
