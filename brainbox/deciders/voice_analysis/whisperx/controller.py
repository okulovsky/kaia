import json
import os
from unittest import TestCase

from ....framework import (
    BrainboxImageBuilder, IImageBuilder,
    BrainBoxApi, BrainBoxTask,
    DockerMarshallingController, RunConfiguration,
)
from .settings import WhisperXSettings
from pathlib import Path


class WhisperXController(DockerMarshallingController[WhisperXSettings]):
    def get_image_builder(self) -> IImageBuilder | None:
        return BrainboxImageBuilder(
            Path(__file__).parent,
            '3.11.11',
            ('ffmpeg',),
            allow_arm64=False,
            custom_apt_installation=(CUDA_RUNTIME_INSTALLATION,),
            dependencies=(
                BrainboxImageBuilder.PytorchDependencies('2.7.1', 'cu128', True),
                BrainboxImageBuilder.RequirementsLockTxt(),
                BrainboxImageBuilder.KaiaFoundationDependencies(),
            ),
        )

    def get_default_settings(self):
        return WhisperXSettings()

    def get_service_run_configuration(self, parameter: str | None) -> RunConfiguration:
        return RunConfiguration(
            publish_ports={self.connection_settings.port: 8080},
        )

    def create_api(self):
        from .api import WhisperXApi
        return WhisperXApi()

    def custom_self_test(self, api: BrainBoxApi, tc: TestCase):
        from .api import WhisperX

        filename = Path(__file__).parent / 'files/sample.mp4'
        hf_token = os.environ['HF_TOKEN']

        task = WhisperX.new_task().execute(filename, hf_token)
        id = api.add(task)
        log_file = api.join(id)

        result = None
        lines = api.cache.read_file(log_file).string_content.split('\n')
        for line in lines:
            if len(line.strip()) > 0:
                js = json.loads(line)
                if js['result'] is not None:
                    result = js['result']

        tc.assertIsNotNone(result)
        tc.assertIsInstance(result, str)
        parsed = json.loads(result)
        tc.assertIn('segments', parsed)


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
