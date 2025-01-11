from typing import Iterable
from unittest import TestCase
from ....framework import (
    RunConfiguration, SmallImageBuilder, IImageBuilder, DockerWebServiceController,
    BrainBoxApi, TestReport
)
from ...common import download_file
from .settings import ComfyUISettings, ComfyUIFile
from pathlib import Path
import os


class ComfyUIController(DockerWebServiceController[ComfyUISettings]):
    def get_image_builder(self) -> IImageBuilder|None:
        main_dependencies = [c.strip() for c in DEPENDENCIES.split('\n') if c.strip()!='']
        extension_dependencies = list(self.settings.extension_requirements)

        return SmallImageBuilder(
            Path(__file__).parent/'container',
            DOCKERFILE,
            [main_dependencies, extension_dependencies]
        )

    def get_service_run_configuration(self, parameter: str|None) -> RunConfiguration:
        if parameter is not None:
            raise ValueError(f"`parameter` must be None for {self.get_name()}")

        return RunConfiguration(
            parameter,
            publish_ports={self.connection_settings.port: 8188},
            mount_resource_folders={
                'hf': '/home/app/.cache/huggingface',
                'output': '/home/app/ComfyUI/output',
                'input': '/home/app/ComfyUI/input',
                'custom_nodes': '/home/app/ComfyUI/custom_nodes',
                'models': '/home/app/ComfyUI/models'
            }
        )


    def get_default_settings(self):
        return ComfyUISettings()

    def create_api(self):
        from .api import ComfyUI
        return ComfyUI()

    def download_file(self, file_desc: ComfyUIFile, override: bool = False):
        if file_desc.models_subfolder is not None:
            folder = self.resource_folder('models') / file_desc.models_subfolder
        elif file_desc.custom_subfolder is not None:
            folder = self.resource_folder(file_desc.custom_subfolder)
        else:
            raise ValueError("Both models_subfolder and custom_subfolder are null")
        file = folder / file_desc.get_filename()
        if file.is_file():
            if not override:
                return
            else:
                os.unlink(file)
        download_file(file_desc.url, str(file))


    def post_install(self):
        self.run_auxiliary_configuration(self.get_service_run_configuration(None).as_service_worker('--fix'))
        for extension in self.settings.extensions:
            arguments = ['--install', extension.git_url]
            if extension.commit is not None:
                arguments.extend(['--commit', extension.commit])
            self.run_auxiliary_configuration(self.get_service_run_configuration(None).as_service_worker(*arguments))
        for model in self.settings.models_to_download:
            self.download_file(model)


    def _self_test_internal(self, api: BrainBoxApi, tc: TestCase) -> Iterable:
        from .tests import Test
        yield TestReport.attach_source_file(Test)
        yield from Test(api, tc).test_all()







DOCKERFILE = f'''
FROM python:3.12

{{{SmallImageBuilder.ADD_USER_PLACEHOLDER}}}

{{{SmallImageBuilder.PIP_INSTALL_PLACEHOLDER}}}

WORKDIR /home/app

{SmallImageBuilder.GIT_CLONE_AND_RESET('https://github.com/comfyanonymous/ComfyUI', 'ComfyUI', '669d9e4c67849e380044871788eb2be615a50396', install=False)}

RUN mkdir /home/app/fix && cp -r /home/app/ComfyUI/models /home/app/fix/models && cp -r /home/app/ComfyUI/input /home/app/fix/input

COPY main.py /home/app/main.py

ENTRYPOINT ["python3","/home/app/main.py"]
'''

DEPENDENCIES = '''
--find-links https://download.pytorch.org/whl/torch_stable.html
--extra-index-url https://download.pytorch.org/whl/cu124
aiohappyeyeballs==2.4.3
aiohttp==3.10.10
aiosignal==1.3.1
attrs==24.2.0
certifi==2024.8.30
cffi==1.17.1
charset-normalizer==3.4.0
einops==0.8.0
filelock==3.16.1
frozenlist==1.5.0
fsspec==2024.10.0
huggingface-hub==0.26.1
idna==3.10
Jinja2==3.1.4
kornia==0.7.3
kornia_rs==0.1.5
MarkupSafe==3.0.2
mpmath==1.3.0
multidict==6.1.0
networkx==3.4.2
numpy==2.1.2
nvidia-cublas-cu12==12.4.5.8
nvidia-cuda-cupti-cu12==12.4.127
nvidia-cuda-nvrtc-cu12==12.4.127
nvidia-cuda-runtime-cu12==12.4.127
nvidia-cudnn-cu12==9.1.0.70
nvidia-cufft-cu12==11.2.1.3
nvidia-curand-cu12==10.3.5.147
nvidia-cusolver-cu12==11.6.1.9
nvidia-cusparse-cu12==12.3.1.170
nvidia-nccl-cu12==2.21.5
nvidia-nvjitlink-cu12==12.4.127
nvidia-nvtx-cu12==12.4.127
packaging==24.1
pillow==11.0.0
propcache==0.2.0
psutil==6.1.0
pycparser==2.22
PyYAML==6.0.2
regex==2024.9.11
requests==2.32.3
safetensors==0.4.5
scipy==1.14.1
sentencepiece==0.2.0
setuptools==75.2.0
soundfile==0.12.1
spandrel==0.4.0
sympy==1.13.1
tokenizers==0.20.1
torch==2.5.0+cu124
torchaudio==2.5.0+cu124
torchsde==0.2.6
torchvision==0.20.0+cu124
tqdm==4.66.5
trampoline==0.1.2
transformers==4.46.0
triton==3.1.0
typing_extensions==4.12.2
urllib3==2.2.3
yarl==1.16.0
'''