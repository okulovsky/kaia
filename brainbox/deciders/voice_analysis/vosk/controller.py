from typing import Iterable
from unittest import TestCase
from ....framework import (
    RunConfiguration, TestReport, BrainboxImageBuilder, IImageBuilder, DockerWebServiceController,
    BrainBoxApi, BrainBoxTask, FileIO, INotebookableController, IModelDownloadingController, DownloadableModel,
    File
)
from .settings import VoskSettings
from .model import VoskModel
from pathlib import Path


class VoskController(
    DockerWebServiceController[VoskSettings],
    INotebookableController,
    IModelDownloadingController
):
    def get_image_builder(self) -> IImageBuilder|None:
        return BrainboxImageBuilder(
            Path(__file__).parent,
            '3.9.21',
            ('ffmpeg',),
            allow_arm64=True
        )

    def get_service_run_configuration(self, parameter: str|None) -> RunConfiguration:
        if parameter is not None:
            raise ValueError(f"`parameter` must be None for {self.get_name()}")
        return RunConfiguration(
            publish_ports={self.connection_settings.port:8080},
            mount_resource_folders={
                'models': '/models'
            }
        )

    def get_notebook_configuration(self) -> RunConfiguration|None:
        return self.get_service_run_configuration(None).as_notebook_service()

    def get_default_settings(self):
        return VoskSettings()

    def get_downloadable_model_type(self) -> type[DownloadableModel]:
        return VoskModel

    def create_api(self):
        from .api import Vosk
        return Vosk()

    def post_install(self):
        self.download_models(self.settings.models_to_download)

    def _self_test_internal(self, api: BrainBoxApi, tc: TestCase) -> Iterable:
        from .api import Vosk
        file = File.read(Path(__file__).parent/'files/test_voice.wav')
        result = api.execute(BrainBoxTask.call(Vosk).transcribe(file, 'en'))
        tc.assertEqual(1, len(result))
        tc.assertEqual('one little spark and before you know it the whole world is burning', result[0]['text'])
        tc.assertEqual(13, len(result[0]['result']))
        tc.assertIn('conf', result[0]['result'][0])
        tc.assertIn('start', result[0]['result'][0])
        tc.assertIn('end', result[0]['result'][0])
        tc.assertIn('word', result[0]['result'][0])

        yield (
            TestReport
            .last_call(api)
        )

        api.execute(BrainBoxTask.call(Vosk).transcribe_to_array(file, 'en'))
        yield (
            TestReport
            .last_call(api)
        )

