import os
from typing import *
from .settings import TortoiseTTSSettings
from ..arch import LocalImageInstaller, BrainBoxServiceRunner, DockerService
from ..arch.utils import check_if_its_sound
from ...deployment import SmallImageBuilder, LocalExecutor
from unittest import TestCase
from pathlib import Path
from kaia.brainbox.deciders.tortoise_tts.api import TortoiseTTS
from kaia.infra import Loc
from ...core import BrainBoxApi, BrainBoxTask, IntegrationTestResult


class TortoiseTTSInstaller(LocalImageInstaller):
    def __init__(self, settings: TortoiseTTSSettings):
        self.settings = settings

        service = DockerService(
            self, self.settings.port, self.settings.startup_time_in_seconds,
            BrainBoxServiceRunner(
                publish_ports={self.settings.port:8084},
                mount_resource_folders=dict(
                    voices = '/home/app/tortoise/tortoise/voices',
                    hf_models = '/home/app/.cache/huggingface/hub/',
                    tortoise_models = '/home/app/.cache/tortoise/models',
                    stash = '/stash'
                ),
                gpu_required=BrainBoxServiceRunner.GpuRequirement.Mandatory,
                vram_in_gb_required=10
            )
        )

        super().__init__(
            'tortoise-tts',
            Path(__file__).parent/'container',
            DOCKERFILE,
            None,
            service
        )

        self.install_service = service.as_service_worker('--install')
        self.notebook_service = service.as_notebook_service()


    def create_api(self):
        return TortoiseTTS(f'{self.settings.address}:{self.settings.port}', self.resource_folder('stash'))

    def get_voice_path(self, voice = None):
        return self.resource_folder('voices',voice)

    def export_voice(self, voice: str, files: Union[Path, Iterable[Path]]):
        if voice is None:
            raise ValueError("Voice cannot be None")

        if isinstance(files, Path):
            from yo_fluq_ds import Query
            files = Query.folder(files).to_list()

        tortoise_folder = self.get_voice_path(voice)
        self.executor.delete_file_or_folder(tortoise_folder)
        self.executor.create_empty_folder(tortoise_folder)
        for file in files:
            tortoise_file = tortoise_folder / (file.name + '.wav')
            tmp_file = Loc.temp_folder/'tortoise_tts_export'/(file.name+'.wav')
            os.makedirs(tmp_file.parent, exist_ok=True)
            LocalExecutor().execute(['ffmpeg', '-i', file, '-ar', '22050', tmp_file, '-y'])
            self.executor.upload_file(tmp_file, tortoise_file)


    def _brainbox_self_test_internal(self, api: BrainBoxApi, tc: TestCase):
        self.export_voice('test_voice', [Path(__file__).parent/'test_voice.wav'])
        text = IntegrationTestResult.VOICEOVER_SAMPLE+' - voice clone with Tortoise.'
        files = api.execute(BrainBoxTask.call(TortoiseTTS).dub(text=text, voice='test_voice'))
        yield IntegrationTestResult(0, None, text)
        for i, file in enumerate(files):
            file = api.pull_content(file)
            check_if_its_sound(file, tc)
            yield IntegrationTestResult(0, None, file)


    def post_install(self):
        pass
        #self.install_service.run()



DOCKERFILE = f'''
FROM nvidia/cuda:12.2.0-base-ubuntu22.04

COPY . /app

RUN apt-get update && \
    apt-get install -y --allow-unauthenticated --no-install-recommends \
    wget \
    git \
    && apt-get autoremove -y \
    && apt-get clean -y \
    && rm -rf /var/lib/apt/lists/*
    
{{{SmallImageBuilder.ADD_USER_PLACEHOLDER}}}

RUN wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O /tmp/miniconda3.sh \
    && bash /tmp/miniconda3.sh -b -p "/home/app/conda" -f -u \
    && "/home/app/conda/bin/conda" init bash \
    && rm -f /tmp/miniconda3.sh \
    && echo ". '/home/app/conda/etc/profile.d/conda.sh'" >> "/home/app/.profile"


ENV PATH="/home/app/conda/bin":$PATH
ENV CONDA_AUTO_UPDATE_CONDA=false

# --login option used to source bashrc (thus activating conda env) at every RUN statement
SHELL ["/bin/bash", "--login", "-c"]

RUN git clone https://github.com/neonbjb/tortoise-tts.git /home/app/tortoise

WORKDIR /home/app/tortoise

RUN conda create --name tortoise python=3.9 numba inflect -y \
    && conda activate tortoise \
    && conda install --yes pytorch==2.2.2 torchvision==0.17.2 torchaudio==2.2.2 pytorch-cuda=12.1 -c pytorch -c nvidia \
    && conda install --yes transformers=4.31.0 
    
RUN /home/app/conda/envs/tortoise/bin/pip install -r requirements.txt 
 
RUN /home/app/conda/envs/tortoise/bin/pip install flask notebook

COPY . /home/app/tortoise/

RUN rm setup.py

RUN /home/app/conda/envs/tortoise/bin/pip install -e .

ENTRYPOINT ["/home/app/conda/envs/tortoise/bin/python", "/home/app/tortoise/main.py"]

'''
