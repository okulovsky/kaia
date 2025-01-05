from typing import Iterable
from unittest import TestCase
from ....framework import (
    RunConfiguration, TestReport, SmallImageBuilder, IImageBuilder,
    BrainBoxApi, BrainBoxTask, File,
    OnDemandDockerController
)
from .settings import VideoToImagesSettings
from pathlib import Path



class VideoToImagesController(OnDemandDockerController[VideoToImagesSettings]):
    def get_image_builder(self) -> IImageBuilder|None:
        return SmallImageBuilder(
            Path(__file__).parent/'container',
            DOCKERFILE,
            DEPENDENCIES.split('\n'),
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

    def get_run_configuration(self, arguments: list[str]):
        return RunConfiguration(
            None,
            command_line_arguments=arguments,
            detach=False,
            interactive=False,
            dont_rm=True,
            mount_resource_folders={
                'cache' : '/home/app/.cache'
            }
        )


    def _self_test_internal(self, api: BrainBoxApi, tc: TestCase) -> Iterable:
        from .api import VideoToImages

        VideoToImages.upload_video(Path(__file__).parent/'sample.mp4').execute(api)
        api.execute(BrainBoxTask.call(VideoToImages).process('sample.mp4', cap_result_count=5))
        yield TestReport.last_call(api).href('run').result_is_array_of_files(File.Kind.Image)








DOCKERFILE = f"""
FROM python:3.11

{{{SmallImageBuilder.ADD_USER_PLACEHOLDER}}}

WORKDIR /home/app

{{{SmallImageBuilder.PIP_INSTALL_PLACEHOLDER}}}

COPY . /home/app

ENTRYPOINT ["python3", "/home/app/main.py"]
"""

DEPENDENCIES = """
annotated-types==0.7.0
anyio==4.5.2
certifi==2019.11.28
chardet==3.0.4
click==8.1.7
dbus-next==0.2.3
exceptiongroup==1.2.2
fastapi==0.115.3
filelock==3.16.1
fsspec==2024.10.0
h11==0.14.0
huggingface-hub==0.27.0
idna==2.8
Jinja2==3.1.4
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
pydantic_core==2.23.4
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
typing_extensions==4.12.2
urllib3==1.25.8
uvicorn==0.32.0
"""