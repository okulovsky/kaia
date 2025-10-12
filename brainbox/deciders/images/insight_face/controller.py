from typing import Iterable
from unittest import TestCase
from ....framework import (
    RunConfiguration, TestReport, BrainboxImageBuilder, IImageBuilder, DockerWebServiceController,
    BrainBoxApi, BrainBoxTask, INotebookableController, File, SmallImageBuilder
)
from .settings import InsightFaceSettings
from pathlib import Path
import os

class InsightFaceController(
    DockerWebServiceController[InsightFaceSettings],
    INotebookableController
):
    def get_image_builder(self) -> IImageBuilder|None:
        return BrainboxImageBuilder(
            Path(__file__).parent,
            '3.11.11',
            allow_arm64=True
        )


    def get_service_run_configuration(self, parameter: str|None) -> RunConfiguration:
        if parameter is not None:
            raise ValueError(f"`parameter` must be None for {self.get_name()}")
        config = RunConfiguration(
            publish_ports={self.settings.connection.port: 8084},
        )
        return config

    def get_notebook_configuration(self) -> RunConfiguration|None:
        return self.get_service_run_configuration(None).as_notebook_service()

    def get_default_settings(self):
        return InsightFaceSettings()

    def create_api(self):
        from .api import InsightFace
        return InsightFace()

    def post_install(self):
        pass


    def _self_test_internal(self, api: BrainBoxApi, tc: TestCase) -> Iterable:
        from .api import InsightFace
        file = File.read(Path(__file__).parent / 'files/image.png')


        result = api.execute(BrainBoxTask.call(InsightFace).analyze(image=file))
        yield TestReport.last_call(api)

        tc.assertEqual(5, len(result))

