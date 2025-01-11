from .settings import PiperSettings
from ..arch import LocalImageInstaller, DockerService, BrainBoxServiceRunner
from ..arch.utils import check_if_its_sound
from ...core import BrainBoxApi, BrainBoxTask, File, IntegrationTestResult
from ...core import BrainBoxTaskPack
from unittest import TestCase
from pathlib import Path
import requests
import json

from .api import Piper

DEPENDENCIES = """
fastapi
uvicorn
pydantic
requests
"""

DOCKERFILE = f"""
FROM lscr.io/linuxserver/piper:latest
# USER root
RUN apt-get update \
 && apt-get install -y python3 python3-pip \
 && apt-get install -y python3 python3-pip wget \
 && rm -rf /var/lib/apt/lists/*

RUN pip install fastapi uvicorn pydantic requests

WORKDIR /
RUN mkdir -p /audio_files && chmod 777 /audio_files
RUN mkdir -p /app
RUN mkdir -p /config \
 && chown -R 20:20 /config \
 && chmod -R 775 /config

COPY server.py /app/server.py
COPY main.py /app/main.py

ENTRYPOINT ["python3", "/app/main.py"]

"""

class PiperInstaller(LocalImageInstaller):
    def __init__(self, settings: PiperSettings):
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
            name="piper",                         
            path_to_container_code=Path(__file__).parent / "container",  
            dockerfile_template=DOCKERFILE,
            dependency_listing=DEPENDENCIES,
            main_service=service
        )

    def create_api(self) -> Piper:
        return Piper(f"{self.ip_address}:{self.settings.port}")

    def _brainbox_self_test_internal(self, api: BrainBoxApi, tc: TestCase):
        task_download = BrainBoxTask.call(Piper).download_model(
        name="en_GB-alba-medium",
        config_url="https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_GB/alan/medium/en_GB-alan-medium.onnx.json?download=true",
        url="https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_GB/alba/medium/en_GB-alba-medium.onnx"
        )
        api.execute(task_download)

        text = IntegrationTestResult.VOICEOVER_SAMPLE
        yield IntegrationTestResult(0, None, text)

        task = BrainBoxTask.call(Piper).voiceover(
            text=text,
            model_path="/config/en_GB-alba-medium.onnx"
        )
        result_file = api.execute(task)
        tc.assertIsInstance(result_file, File)
        result_file = api.pull_content(result_file)
        check_if_its_sound(result_file, tc)
        yield IntegrationTestResult(0, None, result_file)
