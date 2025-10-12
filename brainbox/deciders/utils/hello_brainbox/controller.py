from typing import Iterable
from unittest import TestCase
from ....framework import (
    RunConfiguration, TestReport, BrainboxImageBuilder, IImageBuilder, DockerWebServiceController,
    BrainBoxApi, BrainBoxTask, FileIO, INotebookableController, IModelDownloadingController, DownloadableModel
)
from .settings import HelloBrainBoxSettings
from .model import HelloBrainBoxModel
from pathlib import Path


class HelloBrainBoxController(
    DockerWebServiceController[HelloBrainBoxSettings],
    INotebookableController,
    IModelDownloadingController
):
    def get_image_builder(self) -> IImageBuilder|None:
        return BrainboxImageBuilder(
            Path(__file__).parent,
            '3.11.11'
        )

    def get_downloadable_model_type(self) -> type[DownloadableModel]:
        return HelloBrainBoxModel

    def get_service_run_configuration(self, parameter: str|None) -> RunConfiguration:
        if parameter is None:
            parameter = 'no_parameter'
        return RunConfiguration(
            parameter,
            publish_ports={self.connection_settings.port:8080},
            command_line_arguments=['--setting', self.settings.setting, '--parameter', parameter],
        )

    def get_notebook_configuration(self) -> RunConfiguration|None:
        return self.get_service_run_configuration('').as_notebook_service()

    def get_default_settings(self):
        return HelloBrainBoxSettings()

    def create_api(self):
        from .api import HelloBrainBox
        return HelloBrainBox()

    def post_install(self):
        FileIO.write_text("HelloBrainBox resource", self.resource_folder()/'resource')
        FileIO.write_text("HelloBrainBox nested resource", self.resource_folder('nested') / 'resource')


    def _self_test_internal(self, api: BrainBoxApi, tc: TestCase) -> Iterable:
        from .api import HelloBrainBox

        api.execute(BrainBoxTask.call(HelloBrainBox, 'test_parameter').json('test_argument_json'))


        yield (
            TestReport
            .last_call(api)
            .href('json')
            .with_comment("Returns JSON as a string. This string is stored in the database")
        )

        api.execute(BrainBoxTask.call(HelloBrainBox, 'test_parameter').file('test_argument_file'))
        yield (
            TestReport
            .last_call(api)
            .href('file')
            .result_is_file()
            .with_comment("Returns a json as a file. It's content is not stored in the database, but in the file cache")
        )

        api.execute(BrainBoxTask.call(HelloBrainBox, 'test_parameter').resources())
        yield (
            TestReport
            .last_call(api)
            .href('resources')
            .with_comment("Returns a json with the list of resources: files that are stored at the server outside of the cache, and are shared with the container")
        )

