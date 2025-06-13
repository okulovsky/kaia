from typing import Iterable
from unittest import TestCase

from ....framework import (
    TestReport, SmallImageBuilder, IImageBuilder,
    BrainBoxApi, BrainBoxTask,
    OnDemandDockerController
)
from .settings import WhisperXSettings
from pathlib import Path



class WhisperXController(OnDemandDockerController[WhisperXSettings]):
    def get_image_builder(self) -> IImageBuilder|None:
        return SmallImageBuilder(
            Path(__file__).parent/'container',
            DOCKERFILE,
            DEPENDENCIES.split('\n'),
        )

    def get_default_settings(self):
        return WhisperXSettings()

    def create_api(self):
        from .api import WhisperX
        return WhisperX()

    def _self_test_internal(self, api: BrainBoxApi, tc: TestCase) -> Iterable:
        from .api import WhisperX

        filename = Path(__file__).parent/'files/sample.mp4'
        api.execute(BrainBoxTask.call(WhisperX).execute(filename))
        yield TestReport.last_call(api).href('run')




DOCKERFILE = f"""
FROM python:3.11.11

# Add NVIDIA APT repo and install cuDNN + CUDA runtime
RUN apt-get update && apt-get install -y curl gnupg && \
    mkdir -p /etc/apt/keyrings && \
    curl -fsSL https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/3bf863cc.pub \
    | gpg --dearmor -o /etc/apt/keyrings/cuda-archive-keyring.gpg && \
    echo "deb [signed-by=/etc/apt/keyrings/cuda-archive-keyring.gpg] https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64 /" \
    > /etc/apt/sources.list.d/cuda.list && \
    apt-get update && \
    apt-get install -y libcudnn8=8.9.4.* cuda-runtime-12-1 && \
    apt-get clean && rm -rf /var/lib/apt/lists/*
    
{SmallImageBuilder.APT_INSTALL('ffmpeg')}

{{{SmallImageBuilder.ADD_USER_PLACEHOLDER}}}

WORKDIR /home/app

{{{SmallImageBuilder.PIP_INSTALL_PLACEHOLDER}}}

COPY . .

ENTRYPOINT ["python3", "/home/app/main.py"]
"""

DEPENDENCIES = """
--extra-index-url https://download.pytorch.org/whl/cu121
aiohappyeyeballs==2.6.1
aiohttp==3.12.12
aiosignal==1.3.2
alembic==1.16.1
antlr4-python3-runtime==4.9.3
asteroid-filterbanks==0.4.0
attrs==25.3.0
av==14.4.0
certifi==2025.4.26
cffi==1.17.1
charset-normalizer==3.4.2
click==8.2.1
coloredlogs==15.0.1
colorlog==6.9.0
contourpy==1.3.2
ctranslate2==4.4.0
cycler==0.12.1
docopt==0.6.2
einops==0.8.1
faster-whisper==1.1.1
filelock==3.18.0
flatbuffers==25.2.10
fonttools==4.58.2
frozenlist==1.7.0
fsspec==2025.5.1
greenlet==3.2.3
hf-xet==1.1.2
huggingface-hub==0.33.0
humanfriendly==10.0
HyperPyYAML==1.2.2
idna==3.10
Jinja2==3.1.6
joblib==1.5.1
julius==0.2.7
kiwisolver==1.4.8
lightning==2.5.1.post0
lightning-fabric==2.0.4
lightning-utilities==0.14.3
Mako==1.3.10
markdown-it-py==3.0.0
MarkupSafe==3.0.2
matplotlib==3.10.3
mdurl==0.1.2
mpmath==1.3.0
multidict==6.4.4
networkx==3.5
nltk==3.9.1
numpy==2.3.0
nvidia-cublas-cu12==12.6.4.1
nvidia-cuda-cupti-cu12==12.6.80
nvidia-cuda-nvrtc-cu12==12.6.77
nvidia-cuda-runtime-cu12==12.6.77
nvidia-cudnn-cu12==9.5.1.17
nvidia-cufft-cu12==11.3.0.4
nvidia-cufile-cu12==1.11.1.6
nvidia-curand-cu12==10.3.7.77
nvidia-cusolver-cu12==11.7.1.2
nvidia-cusparse-cu12==12.5.4.2
nvidia-cusparselt-cu12==0.6.3
nvidia-nccl-cu12==2.26.2
nvidia-nvjitlink-cu12==12.6.85
nvidia-nvtx-cu12==12.6.77
omegaconf==2.3.0
onnxruntime==1.22.0
optuna==4.3.0
packaging==24.2
pandas==2.3.0
pillow==11.2.1
primePy==1.3
propcache==0.3.2
protobuf==6.31.1
pyannote.audio==3.3.2
pyannote.core==5.0.0
pyannote.database==5.1.3
pyannote.metrics==3.2.1
pyannote.pipeline==3.0.1
pycparser==2.22
Pygments==2.19.1
pyparsing==3.2.3
python-dateutil==2.9.0.post0
pytorch-lightning==2.5.1.post0
pytorch-metric-learning==2.8.1
pytz==2025.2
PyYAML==6.0.2
regex==2024.11.6
requests==2.32.4
rich==14.0.0
ruamel.yaml==0.18.14
ruamel.yaml.clib==0.2.12
safetensors==0.5.3
scikit-learn==1.7.0
scipy==1.15.3
semver==3.0.4
sentencepiece==0.2.0
shellingham==1.5.4
six==1.17.0
sortedcontainers==2.4.0
soundfile==0.13.1
speechbrain==1.0.3
SQLAlchemy==2.0.41
sympy==1.14.0
tabulate==0.9.0
tensorboardX==2.6.4
threadpoolctl==3.6.0
tokenizers==0.21.1
torch==2.7.1
torch-audiomentations==0.12.0
torch_pitch_shift==1.2.5
torchaudio==2.7.1
torchmetrics==1.7.2
tqdm==4.67.1
transformers==4.52.4
triton==3.3.1
typer==0.16.0
typing_extensions==4.14.0
tzdata==2025.2
urllib3==2.4.0
whisperx==3.3.4
yarl==1.20.1
"""


ORIGINAL_DEPENDENCIES = """
whisperx==3.3.4
lightning_fabric==2.0.4
hf_xet==1.1.2
"""