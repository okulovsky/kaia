import os
from pathlib import Path
from .settings import ComfyUISettings, ComfyUIFile
from ..arch import LocalImageInstaller, DockerService, BrainBoxServiceRunner
from ...deployment import SmallImageBuilder
from unittest import TestCase
from kaia.brainbox.media_library import MediaLibrary
from ...core import BrainBoxApi, BrainBoxTask, IntegrationTestResult, File, BrainBoxTaskPack
from ..collector import Collector
from .api import ComfyUI
import json
from .workflows import TextToImage, Upscale, WD14Interrogate
from uuid import uuid4

class ComfyUIInstaller(LocalImageInstaller):
    def __init__(self, settings: ComfyUISettings):
        self.settings = settings

        runner = BrainBoxServiceRunner(
                publish_ports={self.settings.port: 8188},
                mount_resource_folders={
                    'hf': '/home/app/.cache/huggingface',
                    'output': '/home/app/ComfyUI/output',
                    'input': '/home/app/ComfyUI/input',
                    'custom_nodes': '/home/app/ComfyUI/custom_nodes'
                },
                gpu_required=BrainBoxServiceRunner.GpuRequirement.Mandatory,
            )

        service = DockerService(
            self,
            self.settings.port,
            self.settings.startup_time_in_seconds,
            runner
        )
        main_dependencies = [c.strip() for c in DEPENDENCIES.split('\n') if c.strip()!='']
        extension_dependencies = list(self.settings.extension_requirements)
        super().__init__(
            'comfyui',
            Path(__file__).parent / 'container',
            DOCKERFILE,
            None,
            service,
            custom_dependencies=[main_dependencies, extension_dependencies]
        )
        if self.settings.custom_models_folder is not None:
            self._models_folder = self.settings.custom_models_folder
        else:
            self._models_folder = self.resource_folder('models')
            
        runner.mount_custom_folders = {
            self._models_folder: '/home/app/ComfyUI/models'
        }

    def download_file(self, file_desc: ComfyUIFile, override: bool = False):
        if file_desc.models_subfolder is not None:
            folder = self._models_folder / file_desc.models_subfolder
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
        self._executor.execute(['curl', '-L', file_desc.url, '--output', str(file)])


    def post_install(self):
        self.main_service.as_service_worker('--fix').run()
        for extension in self.settings.extensions:
            arguments = ['--install', extension.git_url]
            if extension.commit is not None:
                arguments.extend(['--commit', extension.commit])
            self.main_service.as_service_worker(*arguments).run()
        for model in self.settings.models_to_download:
            self.download_file(model)

    def create_brainbox_decider_api(self, parameters: str) -> ComfyUI:
        return ComfyUI(
            f'{self.ip_address}:{self.settings.port}',
            self.resource_folder('input'),
            self.resource_folder('output'),
        )

    def create_api(self) -> ComfyUI:
        return ComfyUI(
            f'{self.ip_address}:{self.settings.port}',
            self.resource_folder('input'),
            self.resource_folder('output'),
        )

    def _brainbox_self_test_internal(self, api: BrainBoxApi, tc: TestCase):
        yield IntegrationTestResult(0, "Text to image")
        prompt = "cute little cat playing with a woolball, solo, no humans, animal, cat"
        yield IntegrationTestResult(1, "Prompt", prompt)
        negative_prompt = "bad quality, dull colors, monochrome, boy, girl, people, nsfw, nudity"
        yield IntegrationTestResult(1, "Negative prompt", negative_prompt)

        model_name = 'meinamix_meinaV9.safetensors'
        yield IntegrationTestResult(2, f"Model {model_name}")
        task = TextToImage(
            prompt=prompt,
            negative_prompt=negative_prompt,
            batch_size=2,
            model = model_name,
            seed=42

        ).as_brainbox_task()

        results = api.execute(task)
        for result in results:
            api.pull_content(result)
            yield IntegrationTestResult(2, None, result)

        yield IntegrationTestResult(2, f"With LoRA")
        task = TextToImage(
            prompt=prompt,
            negative_prompt=negative_prompt,
            batch_size=2,
            lora_01='cat_lora.safetensors',
            model=model_name
        ).as_brainbox_task()

        results = api.execute(task)
        for result in results:
            api.pull_content(result)
            yield IntegrationTestResult(2, None, result)

        yield IntegrationTestResult(0, "Upscale")

        source_image = Path(__file__).parent/'image.png'
        input_name = str(uuid4())+'.png'
        yield IntegrationTestResult(1, "Source image", File.read(source_image))

        api.upload(input_name, source_image)
        upscaled = api.execute(Upscale(input_name).as_brainbox_task())
        yield IntegrationTestResult(1, "Upscaled image", api.pull_content(upscaled))

        yield IntegrationTestResult(0, "WD14 Interrogate")
        yield IntegrationTestResult(1, "Source image", File.read(source_image))
        interrogation = api.execute(WD14Interrogate(input_name).as_brainbox_task())
        yield IntegrationTestResult(1, interrogation)






DOCKERFILE = f'''
FROM python:3.12

{{{SmallImageBuilder.ADD_USER_PLACEHOLDER}}}

{{{SmallImageBuilder.PIP_INSTALL_PLACEHOLDER}}}

WORKDIR /home/app

RUN git clone https://github.com/comfyanonymous/ComfyUI

WORKDIR /home/app/ComfyUI

RUN git reset --hard 669d9e4c67849e380044871788eb2be615a50396

RUN mkdir /home/app/fix

RUN cp -r /home/app/ComfyUI/models /home/app/fix/models

RUN cp -r /home/app/ComfyUI/input /home/app/fix/input

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