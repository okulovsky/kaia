from typing import Iterable
from unittest import TestCase
from ....framework import (
    RunConfiguration, TestReport, IImageBuilder, DockerWebServiceController,
    BrainBoxApi, INotebookableController, BrainboxImageBuilder
)
from .settings import CoquiTTSSettings
from pathlib import Path


class CoquiTTSController(DockerWebServiceController[CoquiTTSSettings], INotebookableController):
    def get_image_builder(self) -> IImageBuilder|None:
        return BrainboxImageBuilder(
            Path(__file__).parent,
            '3.11.11',
            ('espeak-ng',),
            BrainboxImageBuilder.Repository(
                'https://github.com/coqui-ai/TTS',
                'dbf1a08a0d4e47fdad6172e433eeb34bc6b13b4e',
                '[all,dev,notebooks]'
            ),
            allow_arm64=False
        )

    def get_service_run_configuration(self, parameter: str|None) -> RunConfiguration:
        if parameter is not None:
            raise ValueError(f"`parameter` must be None for {self.get_name()}")
        return RunConfiguration(
            parameter,
            publish_ports={self.connection_settings.port: 8084},
        )

    def get_notebook_configuration(self) -> RunConfiguration|None:
        return self.get_service_run_configuration(None).as_notebook_service()

    def get_default_settings(self):
        return CoquiTTSSettings()

    def create_api(self):
        from .api import CoquiTTS
        return CoquiTTS()

    def post_install(self):
        for model in self.settings.builtin_models_to_download:
            path = self.resource_folder('builtin') / model.due_folder_name
            if not path.is_dir():
                cfg = self.get_service_run_configuration(None).as_service_worker(
                    '--install',
                    model.model_name,
                    '--install-mode',
                    model.mode
                )
                self.run_auxiliary_configuration(cfg)

    def _self_test_internal(self, api: BrainBoxApi, tc: TestCase) -> Iterable:
        from .tests import Test
        yield TestReport.attach_source_file(Test)
        yield from Test(api, tc).test_all(self.settings)





