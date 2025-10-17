from typing import Iterable
from unittest import TestCase
from ....framework import (
    RunConfiguration, TestReport, BrainboxImageBuilder, IImageBuilder, DockerWebServiceController,
    BrainBoxApi, BrainBoxTask, FileIO, INotebookableController, IModelDownloadingController, DownloadableModel
)
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
                BrainboxImageBuilder.CustomDependencies(
                    ('numpy==1.25.2',)
                ),
                BrainboxImageBuilder.Dependencies()
            ),
            keep_dockerfile = True
        )

    def get_service_run_configuration(self, parameter: str|None) -> RunConfiguration:
        if parameter is not None:
            raise ValueError(f"`parameter` must be None for {self.get_name()}")
        return RunConfiguration(
            publish_ports={self.connection_settings.port:8080},
            mount_resource_folders={
                'pretrained': '/home/app/.cache/huggingface'
            }
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

        api.execute(BrainBoxTask.call(Chatterbox).echo('argument'))


        yield (
            TestReport
            .last_call(api)
            .href('echo')
            .with_comment("Returns JSON with passed arguments and `success` fields")
        )


