from typing import Iterable
from unittest import TestCase
from ....framework import (
    RunConfiguration, TestReport, BrainboxImageBuilder, IImageBuilder, DockerWebServiceController,
    BrainBoxApi, BrainBoxTask, INotebookableController, IModelDownloadingController, File, DownloadableModel
)
from .settings import PiperSettings
from pathlib import Path
from ...common import VOICEOVER_TEXT, check_if_its_sound
from .model import PiperModel

class PiperController(
    DockerWebServiceController[PiperSettings],
    IModelDownloadingController
):
    def get_image_builder(self) -> IImageBuilder|None:
        return BrainboxImageBuilder(
            Path(__file__).parent,
            'lscr.io/linuxserver/piper:1.6.3',
            ('python3', 'python3-pip', 'wget'),
            install_requirements_as_root=True,
            allow_arm64=True
        )

    def get_downloadable_model_type(self) -> type[DownloadableModel]:
        return PiperModel

    def post_install(self):
        self.download_models(self.settings.models_to_download)

    def get_service_run_configuration(self, parameter: str|None) -> RunConfiguration:
        if parameter is not None:
            raise ValueError(f"`parameter` must be None for {self.get_name()}")
        return RunConfiguration(
            publish_ports={self.connection_settings.port:8080},
            mount_resource_folders={
                'models' : '/models',
                'cache' : '/cache'
            },
            dont_rm=True
        )

    def get_default_settings(self):
        return PiperSettings

    def create_api(self):
        from .api import Piper
        return Piper()

    def _self_test_internal(self, api: BrainBoxApi, tc: TestCase) -> Iterable:
        from .api import Piper

        task = BrainBoxTask.call(Piper).voiceover(
            text=VOICEOVER_TEXT,
            model="en",
        )
        result_file = api.execute(task)
        yield TestReport.last_call(api).result_is_file(File.Kind.Audio).href('href')
        check_if_its_sound(api.open_file(result_file).content, tc)



