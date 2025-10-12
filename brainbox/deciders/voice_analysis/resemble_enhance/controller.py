from typing import Iterable
from unittest import TestCase
from ....framework import (
    RunConfiguration, TestReport, BrainboxImageBuilder, IImageBuilder, DockerWebServiceController,
    BrainBoxApi, BrainBoxTask, FileIO, INotebookableController, IModelDownloadingController, DownloadableModel,
    File
)
from .settings import ResembleEnhanceSettings
from ...common import check_if_its_sound
from pathlib import Path


class ResembleEnhanceController(
    DockerWebServiceController[ResembleEnhanceSettings],
    INotebookableController,
):
    def get_image_builder(self) -> IImageBuilder|None:
        return BrainboxImageBuilder(
            Path(__file__).parent,
            '3.11.11',
            ('git-lfs','libsndfile1', 'libsndfile1-dev'),
            allow_arm64=True,
        )

    def get_service_run_configuration(self, parameter: str|None) -> RunConfiguration:
        if parameter is not None:
            raise ValueError(f"`parameter` must be None for {self.get_name()}")
        return RunConfiguration(
            publish_ports={self.connection_settings.port:8080},
            mount_resource_folders={
                'uploads' : '/uploads',
                'outputs' : '/outputs',
                'models' : '/home/app/.local/lib/python3.11/site-packages/resemble_enhance/model_repo'
            },
        )

    def get_notebook_configuration(self) -> RunConfiguration|None:
        return self.get_service_run_configuration(None).as_notebook_service()



    def get_default_settings(self):
        return ResembleEnhanceSettings()

    def create_api(self):
        from .api import ResembleEnhance
        return ResembleEnhance()

    def _self_test_internal(self, api: BrainBoxApi, tc: TestCase) -> Iterable:
        from .api import ResembleEnhance

        input = File.read(Path(__file__).parent/'sample_10db.wav')
        result = api.execute(BrainBoxTask.call(ResembleEnhance).process(input))
        for file in result:
            check_if_its_sound(api.open_file(file).content, tc)

        yield (
            TestReport
            .last_call(api)
            .href('10db')
            .result_is_array_of_files(File.Kind.Audio)
        )
