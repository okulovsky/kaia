from typing import Iterable
from unittest import TestCase
from ....framework import (
    RunConfiguration, TestReport, SmallImageBuilder, IImageBuilder, DockerWebServiceController,
    BrainBoxApi, BrainBoxTask, File, IModelDownloadingController, DownloadableModel
)
from .settings import YoloSettings
from .model import YoloModel
from pathlib import Path


class YoloController(DockerWebServiceController[YoloSettings], IModelDownloadingController):
    def get_image_builder(self) -> IImageBuilder|None:
        return SmallImageBuilder(
            Path(__file__).parent/'container',
            DOCKERFILE,
            DEPENDENCIES.split('\n'),
        )

    def get_downloadable_model_type(self) -> type[DownloadableModel]:
        return YoloModel

    def get_service_run_configuration(self, parameter: str|None) -> RunConfiguration:
        if parameter is not None:
            raise ValueError(f"`parameter` must be None for {self.get_name()}")
        return RunConfiguration(
            parameter,
            publish_ports={self.connection_settings.port:8084},
        )

    def get_default_settings(self):
        return YoloSettings()

    def create_api(self):
        from .api import Yolo
        return Yolo()

    def post_install(self):
        self.download_models(self.settings.models_to_downloads)


    def _self_test_internal(self, api: BrainBoxApi, tc: TestCase) -> Iterable:
        from .api import Yolo

        api.execute(BrainBoxTask.call(Yolo).analyze(
            File.read(Path(__file__).parent / "test_anime_img.png"),
            "Fuyucchi/yolov8_animeface:yolov8x6_animeface.pt"
        ))

        yield TestReport.last_call(api).href('run')





DOCKERFILE = f"""
FROM python:3.11.11

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
    dbus-next
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
    pyparsing==3.1.4
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
    urllib3==1.25.8
    uvicorn==0.32.0
    zipp==3.20.2
"""