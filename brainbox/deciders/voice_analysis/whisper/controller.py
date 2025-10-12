import json
from typing import Iterable
from unittest import TestCase

from ....framework import (
    File, RunConfiguration, TestReport, IImageBuilder, BrainboxImageBuilder,
    DockerWebServiceController, BrainBoxApi, BrainBoxTask, IModelDownloadingController, DownloadableModel
)
from .settings import WhisperSettings, WhisperModel
from pathlib import Path


class WhisperController(DockerWebServiceController[WhisperSettings], IModelDownloadingController):
    def get_image_builder(self) -> IImageBuilder|None:
        return BrainboxImageBuilder(
            Path(__file__).parent,
            '3.9.21',
            ('ffmpeg',),
            allow_arm64=True
        )

    def get_downloadable_model_type(self) -> type[DownloadableModel]:
        return WhisperModel

    def get_service_run_configuration(self, parameter: str|None) -> RunConfiguration:
        if parameter is not None:
            raise ValueError(f"`parameter` must be None for {self.get_name()}")
        return RunConfiguration(
            None,
            publish_ports={self.connection_settings.port:8084},
        )

    def get_notebook_configuration(self) -> RunConfiguration|None:
        return self.get_service_run_configuration(None).as_notebook_service()

    def get_default_settings(self):
        return WhisperSettings()

    def create_api(self):
        from .api import Whisper
        return Whisper()

    def run_notebook(self):
        self.run_with_configuration(self.get_service_run_configuration(None).as_notebook_service())

    def post_install(self):
        self.download_models(self.settings.models_to_download)


    def _self_test_internal(self, api: BrainBoxApi, tc: TestCase) -> Iterable:
        from .api import Whisper

        file = File.read(Path(__file__).parent / 'files/test_voice.wav')

        first_time = True
        for model in self.settings.models_to_download:
            result = api.execute(BrainBoxTask.call(Whisper).transcribe_json(file, model.name))
            yield TestReport.last_call(api).with_comment("Speech recognition with Whisper, full output")
            tc.assertEqual(
                'One little spark and before you know it, the whole world is burning.',
                result['text'].strip()
            )

            result = api.execute(BrainBoxTask.call(Whisper).transcribe(file, model.name))
            if first_time:
                yield TestReport.last_call(api).href('recognition').with_comment("Speech recognition with Whisper, text-only output")
            tc.assertEqual(
                'One little spark and before you know it, the whole world is burning.',
                result
            )

