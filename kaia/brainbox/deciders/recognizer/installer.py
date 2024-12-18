from pathlib import Path
from unittest import TestCase

from loguru import logger

from kaia.brainbox import BrainBoxApi, BrainBoxTask
from kaia.brainbox.deciders.arch import LocalImageInstaller, DockerService, BrainBoxServiceRunner
from .api import RecognizerExtendedAPI, Recognizer
from kaia.brainbox.deployment import SmallImageBuilder
from ...core import IntegrationTestResult


class RecognizerInstaller(LocalImageInstaller):
    def __init__(self, settings):
        self.settings = settings

        service = DockerService(
            self, self.settings.port, self.settings.startup_time_in_seconds,
            BrainBoxServiceRunner(
                publish_ports={self.settings.port:8084},
                gpu_required=BrainBoxServiceRunner.GpuRequirement.No,
            )
        )

        super().__init__(
            'faces-recognizer',
            Path(__file__).parent / 'container',
            DOCKERFILE,
            DEPENDENCIES,
            service
        )

        self.notebook_service = service.as_notebook_service()

    def create_api(self):
        return RecognizerExtendedAPI(f'{self.ip_address}:{self.settings.port}')

    def _brainbox_self_test_internal(self, api: BrainBoxApi, tc: TestCase):
        task1 = BrainBoxTask(
            decider=Recognizer,
            decider_method="post_image",
            arguments={
                "path_to_file": Path(__file__).parent / "container/data/test_anime_img.png"
            }
        )
        result = api.execute(task1)
        tc.assertEqual("OK", result)

        task2 = BrainBoxTask(
                    decider=Recognizer,
                    decider_method="recognize_faces"
                )
        result = api.execute(task2)
        yield IntegrationTestResult(0, "Coords", result)





DOCKERFILE = f"""
FROM ubuntu:20.04

RUN apt-get update
    
RUN apt-get install software-properties-common -y && \
    add-apt-repository ppa:deadsnakes/ppa -y && apt-get update && \
    apt-get install python3.12 -y && apt-get -y install python3-pip
    
RUN apt-get update && apt-get install -y libgl1-mesa-glx && \
    apt-get install -y ffmpeg libsm6 libxext6 && \
    apt-get update && apt-get install ffmpeg libsm6 libxext6  -y

{{{SmallImageBuilder.ADD_USER_PLACEHOLDER}}}

WORKDIR /home/app
    
{{{SmallImageBuilder.PIP_INSTALL_PLACEHOLDER}}}

RUN pip uninstall -y numpy && pip install numpy==1.24.4
COPY . /home/app/

ENTRYPOINT ["python3", "/home/app/main.py"]
"""

DEPENDENCIES = """
    fastapi==0.115.3
    uvicorn==0.32.0
    pydantic==2.9.2
    loguru==0.7.2
    ultralytics==8.3.15
    opencv-contrib-python-headless==4.10.0.82
    huggingface-hub==0.25.1
    python-multipart==0.0.17
"""