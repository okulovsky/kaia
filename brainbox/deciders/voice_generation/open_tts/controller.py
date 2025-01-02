import json
from typing import Iterable
from unittest import TestCase
from ....framework import (
    File, RunConfiguration, TestReport, SmallImageBuilder,
    DockerWebServiceController, IImageSource, RemotePublicImageSource,
    BrainBoxApi, BrainBoxTask
)
from ...common import check_if_its_sound, VOICEOVER_TEXT
from .settings import OpenTTSSettings
from pathlib import Path


class OpenTTSController(DockerWebServiceController[OpenTTSSettings]):
    def get_image_source(self) -> IImageSource:
        return RemotePublicImageSource(
            'synesthesiam/opentts:en',
            self.get_snake_case_name()
        )


    def get_service_run_configuration(self, parameter: str|None) -> RunConfiguration:
        if parameter is not None:
            raise ValueError(f"`parameter` must be None for {self.get_name()}")
        return RunConfiguration(
            parameter,
            publish_ports={self.connection_settings.port: 5500},
            mount_top_resource_folder=False,
        )

    def get_default_settings(self):
        return OpenTTSSettings()

    def create_api(self):
        from .api import OpenTTS
        return OpenTTS()

    def _self_test_internal(self, api: BrainBoxApi, tc: TestCase) -> Iterable:
        from .api import OpenTTS

        result = api.execute(BrainBoxTask.call(OpenTTS).voiceover(VOICEOVER_TEXT))
        yield TestReport.last_call(api).with_comment("Voiceover").result_is_file(File.Kind.Audio)
        result = api.open_file(result)
        check_if_its_sound(result.content, tc)

