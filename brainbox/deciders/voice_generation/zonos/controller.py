import os
from typing import Iterable
from unittest import TestCase
from ....framework import (
    RunConfiguration, TestReport, BrainboxImageBuilder, IImageBuilder, DockerWebServiceController,
    BrainBoxApi, BrainBoxTask, FileIO, INotebookableController, IModelDownloadingController, DownloadableModel,
    File
)
from ...common import VOICEOVER_TEXT, check_if_its_sound
from .settings import ZonosSettings
from pathlib import Path


class ZonosController(
    DockerWebServiceController[ZonosSettings],
    INotebookableController,
):
    def get_image_builder(self) -> IImageBuilder|None:
        return BrainboxImageBuilder(
            Path(__file__).parent,
            'pytorch/pytorch:2.6.0-cuda12.4-cudnn9-devel',
            ('espeak-ng','git','ffmpeg'),
            BrainboxImageBuilder.Repository(
                'https://github.com/Zyphra/Zonos',
                'c6f7704',
            ),
            custom_dependencies=(
                BrainboxImageBuilder.CustomDependencies(
                    ('torch==2.6.0+cu124', 'torchaudio==2.6.0+cu124'),
                    index_url='https://download.pytorch.org/whl/cu124'
                ),
                BrainboxImageBuilder.CustomDependencies(
                    ('mamba-ssm==2.2.4', 'flash_attn==2.7.4.post1', 'causal-conv1d==1.5.0.post8'),
                    no_build_isolation=True,
                    no_binary=('mamba-ssm',),
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
            mount_resource_folders= {
                'cache': '/home/app/.cache',
                'speakers': '/speakers',
                'voices': '/voices'
            },
        )

    def get_notebook_configuration(self) -> RunConfiguration|None:
        return self.get_service_run_configuration(None).as_notebook_service()

    def get_default_settings(self):
        return ZonosSettings()

    def create_api(self):
        from .api import Zonos
        return Zonos()

    def post_install(self):
        path = self.resource_folder('cache')
        if path.is_dir() and len(os.listdir(path))==2:
            print('Already installed')
            return
        self.run_with_configuration(self.get_service_run_configuration(None).as_service_worker('--install'))

    def _self_test_internal(self, api: BrainBoxApi, tc: TestCase) -> Iterable:
        from .api import Zonos

        speaker_sample = File.read(Path(__file__).parent/'app/lina.mp3')
        api.execute(BrainBoxTask.call(Zonos).train('test_speaker', [speaker_sample]))

        yield (
            TestReport
            .last_call(api)
            .href('train')
        )

        result = api.execute(BrainBoxTask.call(Zonos).voiceover(VOICEOVER_TEXT, 'test_speaker'))
        check_if_its_sound(api.open_file(result).content, tc)
        yield (
            TestReport
            .last_call(api)
            .href('voiceover')
            .result_is_file(File.Kind.Audio)
        )

        result = api.execute(BrainBoxTask.call(Zonos).voiceover(VOICEOVER_TEXT, 'test_speaker', speaking_rate=10))
        check_if_its_sound(api.open_file(result).content, tc)
        yield (
            TestReport
            .last_call(api)
            .href('voiceover')
            .result_is_file(File.Kind.Audio)
            .with_comment("Slower speech")
        )

        result = api.execute(BrainBoxTask.call(Zonos).voiceover(VOICEOVER_TEXT, 'test_speaker', speaking_rate=20))
        check_if_its_sound(api.open_file(result).content, tc)
        yield (
            TestReport
            .last_call(api)
            .href('voiceover')
            .result_is_file(File.Kind.Audio)
            .with_comment("Faster speech")
        )


        result = api.execute(BrainBoxTask.call(Zonos).voiceover(VOICEOVER_TEXT, 'test_speaker', emotion=Zonos.Emotions.Happiness))
        check_if_its_sound(api.open_file(result).content, tc)
        yield (
            TestReport
            .last_call(api)
            .href('voiceover')
            .result_is_file(File.Kind.Audio)
            .with_comment("With emotion")
        )

CUDA_RUNTIME_INSTALLATION = '''
RUN apt-get update && apt-get install -y --no-install-recommends \
      curl ca-certificates git ffmpeg espeak-ng build-essential ninja-build cmake && \
    curl -fsSL -o /tmp/cuda-keyring.deb https://developer.download.nvidia.com/compute/cuda/repos/debian12/x86_64/cuda-keyring_1.1-1_all.deb && \
    dpkg -i /tmp/cuda-keyring.deb && rm -f /tmp/cuda-keyring.deb && \
    apt-get update && apt-get install -y --no-install-recommends cuda-toolkit-12-4 && \
    rm -rf /var/lib/apt/lists/*
'''.strip()