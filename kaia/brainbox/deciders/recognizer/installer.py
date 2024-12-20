import json
from pathlib import Path
from unittest import TestCase



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
        yield IntegrationTestResult(0, "Coords", json.dumps(result, indent=3))


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
    charset-normalizer==3.4.0
    click==8.1.7
    contourpy==1.1.1
    cycler==0.12.1
    dbus-python==1.2.16
    distro-info==0.23+ubuntu1.1
    exceptiongroup==1.2.2
    fastapi==0.115.3
    filelock==3.16.1
    fonttools==4.55.3
    fsspec==2024.10.0
    h11==0.14.0
    huggingface-hub==0.25.1
    idna==2.8
    importlib-resources==6.4.5
    jinja2==3.1.4
    kiwisolver==1.4.7
    loguru==0.7.2
    MarkupSafe==2.1.5
    matplotlib==3.7.5
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
    opencv-python==4.10.0.84
    packaging==24.2
    pandas==2.0.3
    pillow==10.4.0
    psutil==6.1.0
    py-cpuinfo==9.0.0
    pydantic==2.9.2
    pydantic-core==2.23.4
    PyGObject==3.36.0
    pyparsing==3.1.4
    python-apt==2.0.1+ubuntu0.20.4.1
    python-dateutil==2.9.0.post0
    python-multipart==0.0.17
    pytz==2024.2
    PyYAML==6.0.2
    requests==2.32.3
    requests-unixsocket==0.2.0
    scipy==1.10.1
    seaborn==0.13.2
    six==1.14.0
    sniffio==1.3.1
    starlette==0.41.3
    sympy==1.13.3
    torch==2.4.1
    torchvision==0.19.1
    tqdm==4.67.1
    triton==3.0.0
    typing-extensions==4.12.2
    tzdata==2024.2
    ultralytics==8.3.15
    ultralytics-thop==2.0.13
    unattended-upgrades==0.1
    urllib3==1.25.8
    uvicorn==0.32.0
    zipp==3.20.2
"""