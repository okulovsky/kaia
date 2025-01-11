from .settings import OpenVoiceSettings
from ..arch import LocalImageInstaller, DockerService, BrainBoxServiceRunner
from ..arch.utils import check_if_its_sound
from ...core import BrainBoxApi, BrainBoxTask, File, IntegrationTestResult
from ...core import BrainBoxTaskPack
from unittest import TestCase
from pathlib import Path
import requests
import json
from kaia.infra import FileIO

from .api import OpenVoice

DEPENDENCIES = """
fastapi
uvicorn
pydantic
requests
"""

DOCKERFILE = f"""

FROM python:3.9-slim

RUN apt-get update && apt-get install -y     git     unzip     build-essential     ffmpeg     wget     && rm -rf /var/lib/apt/lists/*

ENV NUMBA_CACHE_DIR=/tmp/numba_cache
RUN mkdir -p /tmp/numba_cache && chmod 777 /tmp/numba_cache

ENV HOME=/app
ENV XDG_CACHE_HOME=/app/.cache

RUN mkdir -p /app/.cache && chmod 777 /app/.cache

WORKDIR /app

RUN git clone https://github.com/myshell-ai/OpenVoice.git

WORKDIR /app/OpenVoice
RUN pip install -e .

RUN apt-get update && apt-get install -y wget && rm -rf /var/lib/apt/lists/*
RUN wget https://myshell-public-repo-host.s3.amazonaws.com/openvoice/checkpoints_1226.zip -O /tmp/checkpoints_1226.zip  && unzip /tmp/checkpoints_1226.zip  && rm /tmp/checkpoints_1226.zip

RUN mkdir -p /app/OpenVoice/outputs && chmod 777 /app/OpenVoice/outputs
RUN chown -R 20:20 /app/OpenVoice/outputs

RUN mkdir -p /app/OpenVoice/processed && chmod 777 /app/OpenVoice/processed
RUN chown -R 20:20 /app/OpenVoice/processed

COPY server.py /app/OpenVoice/server.py
COPY main.py /app/OpenVoice/main.py

ENTRYPOINT ["python3", "/app/OpenVoice/main.py"]
"""

class OpenVoiceInstaller(LocalImageInstaller):
    def __init__(self, settings: OpenVoiceSettings):
        self.settings = settings
        service = DockerService(
            installer=self,
            ping_port=self.settings.port,
            startup_timeout_in_seconds=self.settings.startup_time_in_seconds,
            container_runner=BrainBoxServiceRunner(
                publish_ports={self.settings.port: 8080},
                mount_data_folder=True,
            )
        )
        super().__init__(
            name="openvoice",
            path_to_container_code=Path(__file__).parent / "container",
            dockerfile_template=DOCKERFILE,
            dependency_listing=DEPENDENCIES,
            main_service=service
        )

    def create_api(self) -> OpenVoice:
        return OpenVoice(f"{self.ip_address}:{self.settings.port}")

    def _brainbox_self_test_internal(self, api: BrainBoxApi, tc: TestCase):
        source_speaker = Path(__file__).parent/ "nikita.wav"
        reference_speaker = Path(__file__).parent/"lina.wav"
        task = BrainBoxTask.call(OpenVoice).generate(source_speaker, reference_speaker)
        result_file = api.execute(task)

        tc.assertIsInstance(result_file, File)
        result_file = api.pull_content(result_file)
        check_if_its_sound(result_file, tc)
        yield IntegrationTestResult(0, None, result_file)
        FileIO.write_bytes(result_file.content, Path(__file__).parent/'result.wav')
