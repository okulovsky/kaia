from typing import Iterable
from unittest import TestCase
from ....framework import (
    RunConfiguration, TestReport, BrainboxImageBuilder, IImageBuilder,
    BrainBoxApi, BrainBoxTask, File,
    OnDemandDockerController
)
from .settings import VideoToImagesSettings
from pathlib import Path



class VideoToImagesController(OnDemandDockerController[VideoToImagesSettings]):
    def get_image_builder(self) -> IImageBuilder|None:
        return BrainboxImageBuilder(
            Path(__file__).parent,
            '3.11.11',
            allow_arm64=True
        )

    def get_default_settings(self):
        return VideoToImagesSettings()

    def post_install(self):
        if (self.resource_folder('cache')/'huggingface/hub/models--sentence-transformers--clip-ViT-B-32').is_dir():
            return
        self.run_with_configuration(self.get_run_configuration(['--install']))

    def create_api(self):
        from .api import VideoToImages
        return VideoToImages()

    def get_run_configuration(self, arguments: list[str] | None = None):
        if arguments is None:
            arguments = []
        return RunConfiguration(
            None,
            command_line_arguments=arguments,
            detach_and_interactive=False,
            mount_resource_folders={
                'cache' : '/home/app/.cache'
            }
        )


    def _self_test_internal(self, api: BrainBoxApi, tc: TestCase) -> Iterable:
        from .api import VideoToImages

        VideoToImages.upload_video(Path(__file__).parent/'sample.mp4').execute(api)
        result = api.execute(BrainBoxTask.call(VideoToImages).process(VideoToImages.AnalysisSettings(
            'sample.mp4',
            max_produced_frames=5,
        )))
        tc.assertEqual(5, len(result))
        yield TestReport.last_call(api).href('run')


        result = api.execute(BrainBoxTask.call(VideoToImages).process(VideoToImages.AnalysisSettings(
            'sample.mp4',
            max_produced_frames=5,
            add_semantic_comparator=True,
        )))
        tc.assertEqual(5, len(result))
        yield TestReport.last_call(api).href('run-comparator')


        result = api.execute(BrainBoxTask.call(VideoToImages).process(VideoToImages.AnalysisSettings(
            'sample.mp4',
            max_produced_frames=5,
            buffer_by_laplacian_in_ms=500,
        )))
        tc.assertEqual(5, len(result))
        yield TestReport.last_call(api).href('run_bufferer')


