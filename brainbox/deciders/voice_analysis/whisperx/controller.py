from typing import Iterable
from unittest import TestCase

from ....framework import (
    TestReport, BrainboxImageBuilder, IImageBuilder,
    BrainBoxApi, BrainBoxTask,
    OnDemandDockerController
)
from .settings import WhisperXSettings
from pathlib import Path



class WhisperXController(OnDemandDockerController[WhisperXSettings]):
    def get_image_builder(self) -> IImageBuilder|None:
        return BrainboxImageBuilder(
            Path(__file__).parent,
            '3.11.11',
            ('ffmpeg',),
            allow_arm64=False,
            custom_apt_installation=(CUDA_RUNTIME_INSTALLATION,)
        )

    def get_default_settings(self):
        return WhisperXSettings()

    def create_api(self):
        from .api import WhisperX
        return WhisperX()

    def _self_test_internal(self, api: BrainBoxApi, tc: TestCase) -> Iterable:
        from .api import WhisperX

        filename = Path(__file__).parent/'files/sample.mp4'
        api.execute(BrainBoxTask.call(WhisperX).execute(filename))
        yield TestReport.last_call(api).href('run')


CUDA_RUNTIME_INSTALLATION = '''
RUN apt-get update && apt-get install -y curl gnupg && \
    mkdir -p /etc/apt/keyrings && \
    curl -fsSL https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/3bf863cc.pub \
    | gpg --dearmor -o /etc/apt/keyrings/cuda-archive-keyring.gpg && \
    echo "deb [signed-by=/etc/apt/keyrings/cuda-archive-keyring.gpg] https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64 /" \
    > /etc/apt/sources.list.d/cuda.list && \
    apt-get update && \
    apt-get install -y libcudnn8=8.9.4.* cuda-runtime-12-1 && \
    apt-get clean && rm -rf /var/lib/apt/lists/*
'''.strip()