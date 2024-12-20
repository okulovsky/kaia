from pathlib import Path
from unittest import TestCase

from kaia.brainbox import BrainBoxApi, BrainBoxTask
from kaia.brainbox.deciders.arch import LocalImageInstaller, DockerService, BrainBoxServiceRunner
from kaia.brainbox.deployment import SmallImageBuilder
from ...core import IntegrationTestResult
from .api import VideoProcessor


class VideoProcessorInstaller(LocalImageInstaller):
    def __init__(self, settings):
        self.settings = settings

        service = DockerService(
            self, self.settings.port, self.settings.startup_time_in_seconds,
            BrainBoxServiceRunner(
                publish_ports={self.settings.port: 8084},
                gpu_required=BrainBoxServiceRunner.GpuRequirement.No,
            )
        )

        super().__init__(
            'video-processor',
            Path(__file__).parent / 'container',
            DOCKERFILE,
            DEPENDENCIES,
            service
        )

        self.notebook_service = service.as_notebook_service()

    def create_api(self):
        return VideoProcessor(f'{self.ip_address}:{self.settings.port}')

    def _brainbox_self_test_internal(self, api: BrainBoxApi, tc: TestCase):
        task1 = BrainBoxTask(
            decider=VideoProcessor,
            decider_method="processing_video",
            arguments={
                "path_to_file": "uh_krasota.mp4"
            }
        )
        result = api.execute(task1)
        tc.assertEqual("OK", result)

        task2 = BrainBoxTask(
            decider=VideoProcessor,
            decider_method="get_frames",
            arguments={"batch_size": 2}
        )
        results = api.execute(task2)

        # i = 0
        for result in results:
            api.pull_content(result)
            yield IntegrationTestResult(0, None, result)

            # Расскоментируйте, если хотите проверить, что изображение корректно декодируется и сохраняется
            # with open(Path(__file__).parent / f"test{i}.png", "wb") as file:
            #     file.write(result.content)
            # i += 1


DOCKERFILE = f"""
FROM ubuntu:20.04
ENV DEBIAN_FRONTEND noninteractive
RUN apt-get update
RUN apt-get install -y pkg-config && apt-get install -y libcairo2-dev libjpeg-dev libgif-dev

RUN apt-get install software-properties-common -y && \
    add-apt-repository ppa:deadsnakes/ppa -y && apt-get update && \
    apt-get install python3.12 -y && apt-get -y install python3-pip

RUN apt-get update && apt-get install -y libgl1-mesa-glx && \
    apt-get install -y ffmpeg libsm6 libxext6 && \
    apt-get update && apt-get install ffmpeg libsm6 libxext6  -y

{{{SmallImageBuilder.ADD_USER_PLACEHOLDER}}}
WORKDIR /home/app
{{{SmallImageBuilder.PIP_INSTALL_PLACEHOLDER}}}
COPY . /home/app/
ENTRYPOINT ["python3", "/home/app/main.py"]
"""

DEPENDENCIES = """
    annotated-types==0.7.0
    anyio==4.5.2
    certifi==2019.11.28
    chardet==3.0.4
    click==8.1.7
    dbus-python==1.2.16
    distro-info==0.23+ubuntu1.1
    exceptiongroup==1.2.2
    fastapi==0.115.3
    filelock==3.16.1
    fsspec==2024.10.0
    h11==0.14.0
    huggingface-hub==0.27.0
    idna==2.8
    jinja2==3.1.4
    joblib==1.4.2
    loguru==0.7.2
    MarkupSafe==2.1.5
    mpmath==1.3.0
    networkx==3.1
    numpy==1.24.4
    nvidia-cublas-cu12==12.1.3.1
    nvidia-cuda-cupti-cu12==12.1.105
    nvidia-cuda-nvrtc-cu12==12.1.105
    nvidia-cuda-runtime-cu12==12.1.105
    nvidia-cudnn-cu12==9.1.0.70
    nvidia-cufft-cu12==11.0.2.54
    nvidia-curand-cu12==10.3.2.106
    nvidia-cusolver-cu12==11.4.5.107
    nvidia-cusparse-cu12==12.1.0.106
    nvidia-nccl-cu12==2.20.5
    nvidia-nvjitlink-cu12==12.6.85
    nvidia-nvtx-cu12==12.1.105
    opencv-contrib-python-headless==4.10.0.82
    packaging==24.2
    Pillow==10.1.0
    pydantic==2.9.2
    pydantic-core==2.23.4
    PyGObject==3.36.0
    python-apt==2.0.1+ubuntu0.20.4.1
    PyYAML==6.0.2
    regex==2024.11.6
    requests==2.22.0
    requests-unixsocket==0.2.0
    safetensors==0.4.5
    scikit-learn==1.3.2
    scipy==1.10.1
    sentence-transformers==3.2.0
    six==1.14.0
    sniffio==1.3.1
    starlette==0.41.3
    sympy==1.13.3
    threadpoolctl==3.5.0
    tokenizers==0.20.3
    torch==2.4.1
    tqdm==4.67.1
    transformers==4.46.3
    triton==3.0.0
    typing-extensions==4.12.2
    unattended-upgrades==0.1
    urllib3==1.25.8
    uvicorn==0.32.0
"""