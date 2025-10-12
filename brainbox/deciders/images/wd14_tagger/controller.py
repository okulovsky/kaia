from typing import Iterable
from unittest import TestCase
from ....framework import (
    RunConfiguration, TestReport, BrainboxImageBuilder, IImageBuilder, DockerWebServiceController,
    BrainBoxApi, BrainBoxTask, FileIO, INotebookableController, IModelDownloadingController, DownloadableModel,
    File
)
from .settings import WD14TaggerSettings
from .model import WD14TaggerModel
from pathlib import Path
import os

class WD14TaggerController(
    DockerWebServiceController[WD14TaggerSettings],
    IModelDownloadingController,
    INotebookableController
):
    def get_image_builder(self) -> IImageBuilder|None:
        return BrainboxImageBuilder(
            Path(__file__).parent,
            '3.11.11',
            ('ffmpeg', 'libsm6', 'libxext6'),
            BrainboxImageBuilder.Repository(
                "https://github.com/corkborg/wd14-tagger-standalone",
                "f1114c877ed6d1b1311f7e485ec0466d5064eb0c",
            ),
            allow_arm64=True
        )

    def get_downloadable_model_type(self) -> type[DownloadableModel]:
        return WD14TaggerModel

    def get_service_run_configuration(self, parameter: str|None) -> RunConfiguration:
        if parameter is not None:
            raise ValueError(f"`parameter` must be None for {self.get_name()}")
        config = RunConfiguration(
            publish_ports={self.settings.connection.port: 8084},
            mount_resource_folders={'models': '/home/app/.cache/huggingface'},
        )
        if self.settings.cpu_share is not None:
            cpu_count = os.cpu_count()
            config.custom_flags=[f'--cpus={self.settings.cpu_share*cpu_count}']
        return config

    def get_notebook_configuration(self) -> RunConfiguration|None:
        return self.get_service_run_configuration(None).as_notebook_service()

    def get_default_settings(self):
        return WD14TaggerSettings()

    def create_api(self):
        from .api import WD14Tagger
        return WD14Tagger()

    def post_install(self):
        self.download_models(self.settings.models_to_download)

    def _self_test_internal(self, api: BrainBoxApi, tc: TestCase) -> Iterable:
        from .api import WD14Tagger
        file = File.read(Path(__file__).parent / 'image.png')

        model = self.settings.models_to_download[0].name
        api.execute(BrainBoxTask.call(WD14Tagger).interrogate(image=file, model=model))
        yield TestReport.last_call(api)

        api.execute(BrainBoxTask.call(WD14Tagger).tags(model=model, count=10))
        yield TestReport.last_call(api)


