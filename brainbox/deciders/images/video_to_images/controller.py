import json
from unittest import TestCase

from ....framework import (
    BrainboxImageBuilder, IImageBuilder,
    BrainBoxApi, BrainBoxTask,
    DockerMarshallingController, RunConfiguration,
)
from .settings import VideoToImagesSettings
from .app.installer import VideoToImagesInstaller
from foundation_kaia.brainbox_utils import Installer
from pathlib import Path


class VideoToImagesController(DockerMarshallingController[VideoToImagesSettings]):
    def get_image_builder(self) -> IImageBuilder | None:
        return BrainboxImageBuilder(
            Path(__file__).parent,
            '3.11.11',
            allow_arm64=True,
            dependencies=(
                BrainboxImageBuilder.PytorchDependencies('2.7.0', 'cu128'),
                BrainboxImageBuilder.RequirementsLockTxt(),
                BrainboxImageBuilder.KaiaFoundationDependencies(),
            ),
        )

    def get_default_settings(self):
        return VideoToImagesSettings()

    def get_installer(self) -> Installer | None:
        return VideoToImagesInstaller(self.resource_folder())

    def get_service_run_configuration(self, parameter: str | None) -> RunConfiguration:
        return RunConfiguration(
            publish_ports={self.connection_settings.port: 8080},
            dont_rm=False,
            mount_resource_folders={'cache': '/home/app/.cache'},
        )

    def create_api(self):
        from .api import VideoToImagesApi
        return VideoToImagesApi()

    def custom_self_test(self, api: BrainBoxApi, tc: TestCase):
        from .api import VideoToImages

        filename = Path(__file__).parent / 'sample.mp4'

        def run_process(settings):
            task = VideoToImages.new_task().process(filename, settings)
            id = api.add(task)
            log_file = api.join(id)
            result = None
            lines = api.cache.read_file(log_file).string_content.split('\n')
            for line in lines:
                if len(line.strip()) > 0:
                    js = json.loads(line)
                    if js['result'] is not None:
                        result = js['result']
            return result

        result = run_process(VideoToImages.AnalysisSettings(max_produced_frames=5))
        tc.assertEqual(5, len(result))

        tar = api.execute(VideoToImages.new_task().get_tar())
        tc.assertIsNotNone(tar)

        result = run_process(VideoToImages.AnalysisSettings(
            max_produced_frames=5,
            add_semantic_comparator=True,
        ))
        tc.assertEqual(5, len(result))

        result = run_process(VideoToImages.AnalysisSettings(
            max_produced_frames=5,
            buffer_by_laplacian_in_ms=500,
        ))
        tc.assertEqual(5, len(result))
