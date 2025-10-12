from typing import Iterable
from unittest import TestCase
from ....framework import (
    RunConfiguration, TestReport, BrainboxImageBuilder, IImageBuilder, DockerWebServiceController,
    BrainBoxApi, BrainBoxTask, FileIO, INotebookableController, IModelDownloadingController, DownloadableModel
)
from .settings import EspeakPhonemizerSettings
from pathlib import Path


class EspeakPhonemizerController(
    DockerWebServiceController[EspeakPhonemizerSettings],
    INotebookableController,
):
    def get_image_builder(self) -> IImageBuilder|None:
        return BrainboxImageBuilder(
            Path(__file__).parent,
            '3.8.20',
            ('libespeak-ng1',),
            allow_arm64=True
        )

    def get_service_run_configuration(self, parameter: str|None) -> RunConfiguration:
        if parameter is not None:
            raise ValueError(f"`parameter` must be None for {self.get_name()}")
        return RunConfiguration(
            publish_ports={self.connection_settings.port:8080},
        )

    def get_notebook_configuration(self) -> RunConfiguration|None:
        return self.get_service_run_configuration(None).as_notebook_service()

    def get_default_settings(self):
        return EspeakPhonemizerSettings()

    def create_api(self):
        from .api import EspeakPhonemizer
        return EspeakPhonemizer()

    def _self_test_internal(self, api: BrainBoxApi, tc: TestCase) -> Iterable:
        from .api import EspeakPhonemizer

        api.execute(BrainBoxTask.call(EspeakPhonemizer).phonemize("This is some text"))

        yield (
            TestReport
            .last_call(api)
            .href('en-pho')
            .with_comment("Phonemizes one english line")
        )

        api.execute(BrainBoxTask.call(EspeakPhonemizer).phonemize(["This is some text", "This is the second line"]))

        yield (
            TestReport
            .last_call(api)
            .href('en-pho-2')
            .with_comment("Phonemizes several english lines")
        )

        api.execute(BrainBoxTask.call(EspeakPhonemizer).phonemize("Keep the stress marks", stress=True))
        yield (
            TestReport
            .last_call(api)
            .href('stress')
            .with_comment("Phonemizes keeping the stress marks")
        )

        api.execute(BrainBoxTask.call(EspeakPhonemizer).phonemize('Das is ein Satz', language='de'))
        yield (
            TestReport
                .last_call(api)
                .href('de')
                .with_comment("Phonemizes German")
        )


