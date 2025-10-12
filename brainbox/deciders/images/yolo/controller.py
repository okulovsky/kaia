from typing import Iterable
from unittest import TestCase
from ....framework import (
    RunConfiguration, TestReport, BrainboxImageBuilder, IImageBuilder, DockerWebServiceController,
    BrainBoxApi, BrainBoxTask, File, IModelDownloadingController, DownloadableModel
)
from .settings import YoloSettings
from .model import YoloModel
from pathlib import Path


class YoloController(DockerWebServiceController[YoloSettings], IModelDownloadingController):
    def get_image_builder(self) -> IImageBuilder|None:
        return BrainboxImageBuilder(
            Path(__file__).parent,
            '3.11.11',
            allow_arm64=True
        )

    def get_downloadable_model_type(self) -> type[DownloadableModel]:
        return YoloModel

    def get_service_run_configuration(self, parameter: str|None) -> RunConfiguration:
        if parameter is not None:
            raise ValueError(f"`parameter` must be None for {self.get_name()}")
        return RunConfiguration(
            parameter,
            publish_ports={self.connection_settings.port:8084},
        )

    def get_default_settings(self):
        return YoloSettings()

    def create_api(self):
        from .api import Yolo
        return Yolo()

    def post_install(self):
        self.download_models(self.settings.models_to_downloads)


    def _self_test_internal(self, api: BrainBoxApi, tc: TestCase) -> Iterable:
        from .api import Yolo

        api.execute(BrainBoxTask.call(Yolo).analyze(
            File.read(Path(__file__).parent / "test_anime_img.png"),
            "Fuyucchi/yolov8_animeface:yolov8x6_animeface.pt"
        ))

        yield TestReport.last_call(api).href('run')




