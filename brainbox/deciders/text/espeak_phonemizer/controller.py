from typing import Iterable
from ....framework import (
    RunConfiguration, SelfTestCase, BrainboxImageBuilder, IImageBuilder,
    DockerMarshallingController, BrainBoxApi, BrainBoxTask,
)
from .settings import EspeakPhonemizerSettings
from pathlib import Path


class EspeakPhonemizerController(DockerMarshallingController[EspeakPhonemizerSettings]):
    def get_image_builder(self) -> IImageBuilder | None:
        return BrainboxImageBuilder(
            Path(__file__).parent,
            '3.11.11',
            ('libespeak-ng1',),
            allow_arm64=True,
            dependencies=(
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

    def get_default_settings(self):
        return EspeakPhonemizerSettings()

    def create_api(self):
        from .api import EspeakPhonemizerApi
        return EspeakPhonemizerApi()

    def self_test_cases(self) -> Iterable[SelfTestCase]:
        from .api import EspeakPhonemizer
        yield SelfTestCase(EspeakPhonemizer.new_task().phonemize(["This is some text"]), None)
        yield SelfTestCase(EspeakPhonemizer.new_task().phonemize(["This is some text", "This is the second line"]), None)
        yield SelfTestCase(EspeakPhonemizer.new_task().phonemize(["Keep the stress marks"], stress=True), None)
        yield SelfTestCase(EspeakPhonemizer.new_task().phonemize(['Das is ein Satz'], language='de'), None)
