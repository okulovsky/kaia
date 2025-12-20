from typing import Iterable
from unittest import TestCase
from ....framework import (
    RunConfiguration, TestReport, BrainboxImageBuilder, IImageBuilder, DockerWebServiceController,
    BrainBoxApi, BrainBoxTask, FileIO, INotebookableController, IModelDownloadingController, DownloadableModel,
    File
)
from ...common import VOICEOVER_TEXT, check_if_its_sound
from .settings import ChatterboxSettings
from pathlib import Path


class ChatterboxController(
    DockerWebServiceController[ChatterboxSettings],
    INotebookableController,
):
    def get_image_builder(self) -> IImageBuilder|None:
        return BrainboxImageBuilder(
            Path(__file__).parent,
            '3.11.11',
            allow_arm64=True,
            custom_dependencies=(
                BrainboxImageBuilder.PytorchDependencies(
                    '2.7.0', 'cu128', True
                ),
                BrainboxImageBuilder.CustomDependencies(
                    ('numpy==1.25.2',)
                ),
                BrainboxImageBuilder.Dependencies(no_deps=True)
            ),
            keep_dockerfile = True,
        )

    def get_service_run_configuration(self, parameter: str|None) -> RunConfiguration:
        if parameter is not None:
            raise ValueError(f"`parameter` must be None for {self.get_name()}")
        return RunConfiguration(
            publish_ports={self.connection_settings.port:8080},
            mount_resource_folders={
                'pretrained': '/home/app/.cache/huggingface',
                'voices': '/voices',
                'speakers': '/speakers',
                'file_cache': '/file_cache',
            },
            dont_rm=True
        )
    
    def post_install(self):
        if not (self.resource_folder('pretrained')/'hub').is_dir():
            self.run_with_configuration(self.get_service_run_configuration(None).as_service_worker('--install'))
        else:
            print('MODELS are already downloaded')

    def get_notebook_configuration(self) -> RunConfiguration|None:
        return self.get_service_run_configuration(None).as_notebook_service()

    def get_default_settings(self):
        return ChatterboxSettings()

    def create_api(self):
        from .api import Chatterbox
        return Chatterbox()

    def _self_test_internal(self, api: BrainBoxApi, tc: TestCase) -> Iterable:
        from .api import Chatterbox

        speaker_sample = File.read(Path(__file__).parent/'research/yc.wav')
        api.execute(BrainBoxTask.call(Chatterbox).train('test_speaker', speaker_sample))


        yield (
            TestReport
            .last_call(api)
            .href('echo')
            .with_comment("Returns JSON with passed arguments and `success` fields")
        )

        result = api.execute(BrainBoxTask.call(Chatterbox).voiceover(VOICEOVER_TEXT, 'test_speaker'))
        tc.assertIsInstance(result, str)
        #check_if_its_sound(api.open_file(result), tc)
        yield (
            TestReport
            .last_call(api)
            .href('voiceover')
            .result_is_file(File.Kind.Audio)
        )
