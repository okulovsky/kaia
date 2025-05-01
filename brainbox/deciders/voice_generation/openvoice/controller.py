import os
from typing import Iterable
from unittest import TestCase

import requests

from ....framework import (
    RunConfiguration, TestReport, SmallImageBuilder, IImageBuilder, DockerWebServiceController,
    BrainBoxApi, BrainBoxTask, INotebookableController, File
)
from ...common import check_if_its_sound, download_file
from .settings import OpenVoiceSettings
from pathlib import Path
import zipfile


class OpenVoiceController(
    DockerWebServiceController[OpenVoiceSettings],
    INotebookableController,
):
    def get_image_builder(self) -> IImageBuilder|None:
        return SmallImageBuilder(
            Path(__file__).parent/'container',
            DOCKERFILE,
            DEPENDENCIES.split('\n'),
        )

    def get_service_run_configuration(self, parameter: str|None) -> RunConfiguration:
        if parameter is not None:
            raise ValueError(f"`parameter` must be None for {self.get_name()}")
        return RunConfiguration(
            publish_ports={self.connection_settings.port:8080},
            mount_resource_folders={
                'pretrained/model/checkpoints' : '/home/app/checkpoints',
                'models' : '/models',
                'voices': '/voices',
                'temp': '/temp'
            },
        )

    def post_install(self):
        path = self.resource_folder('pretrained')/'checkpoints_1226.zip'
        download_file(
            'https://myshell-public-repo-host.s3.amazonaws.com/openvoice/checkpoints_1226.zip',
            path
        )
        if not zipfile.is_zipfile(path):
            raise zipfile.BadZipFile(f"The file {path} is not a valid zip file.")

        folder = self.resource_folder('pretrained','model')
        os.makedirs(folder, exist_ok=True)
        with zipfile.ZipFile(path, 'r') as zip_ref:
            zip_ref.extractall(folder)



    def get_notebook_configuration(self) -> RunConfiguration|None:
        return self.get_service_run_configuration(None).as_notebook_service()

    def get_default_settings(self):
        return OpenVoiceSettings()

    def create_api(self):
        from .api import OpenVoice
        return OpenVoice()

    def _self_test_internal(self, api: BrainBoxApi, tc: TestCase) -> Iterable:
        from .api import OpenVoice

        reference_speaker = File.read(Path(__file__).parent / "lina.wav")
        api.execute(BrainBoxTask.call(OpenVoice).train('test_voice', [reference_speaker]))
        yield TestReport.last_call(api).href('training').with_comment("Training a model for a reference voice")

        source_speaker = File.read(Path(__file__).parent/"nikita.wav")
        task = BrainBoxTask.call(OpenVoice).generate(source_speaker, 'test_voice')
        result_file = api.execute(task)

        check_if_its_sound(api.open_file(result_file).content, tc)
        yield TestReport.last_call(api).href('href').result_is_file(File.Kind.Audio)



DOCKERFILE = f'''

FROM python:3.9.21-slim

{SmallImageBuilder.APT_INSTALL('git unzip build-essential ffmpeg wget')}

{{{SmallImageBuilder.ADD_USER_PLACEHOLDER}}}

{{{SmallImageBuilder.PIP_INSTALL_PLACEHOLDER}}}

WORKDIR /home/app

{SmallImageBuilder.GIT_CLONE_AND_RESET(
    'https://github.com/myshell-ai/OpenVoice.git',
    'OpenVoice',
    'bb79fa78a5a7a7a3d7602b7f6d48705213a039c7',
)}

COPY . /home/app/OpenVoice/

ENTRYPOINT ["python3", "/home/app/OpenVoice/main.py"]
'''

DEPENDENCIES = '''
aiofiles==23.2.1
altair==5.5.0
annotated-types==0.7.0
anyio==4.8.0
argon2-cffi==23.1.0
argon2-cffi-bindings==21.2.0
arrow==1.3.0
asttokens==3.0.0
async-lru==2.0.4
attrs==25.1.0
audioread==3.0.1
av==10.0.0
babel==2.17.0
beautifulsoup4==4.13.1
bleach==6.2.0
blinker==1.9.0
certifi==2025.1.31
cffi==1.17.1
charset-normalizer==3.4.1
click==8.1.8
cn2an==0.5.22
coloredlogs==15.0.1
comm==0.2.2
contourpy==1.2.1
ctranslate2==3.24.0
cycler==0.12.1
Cython==3.0.11
debugpy==1.8.12
decorator==5.1.1
defusedxml==0.7.1
distro==1.9.0
dtw-python==1.4.4
eng-to-ipa==0.0.2
exceptiongroup==1.2.2
executing==2.2.0
fastapi==0.115.8
faster-whisper==0.9.0
fastjsonschema==2.21.1
ffmpy==0.5.0
filelock==3.17.0
Flask==3.1.0
flatbuffers==25.1.24
fonttools==4.55.8
fqdn==1.5.1
fsspec==2025.2.0
gradio==3.48.0
gradio_client==0.6.1
h11==0.14.0
httpcore==1.0.7
httpx==0.28.1
huggingface-hub==0.17.3
humanfriendly==10.0
idna==3.10
importlib_metadata==8.6.1
importlib_resources==6.5.2
inflect==7.0.0
ipykernel==6.29.5
ipython==8.18.1
isoduration==20.11.0
itsdangerous==2.2.0
jedi==0.19.2
jieba==0.42.1
Jinja2==3.1.5
jiter==0.8.2
joblib==1.4.2
json5==0.10.0
jsonpointer==3.0.0
jsonschema==4.23.0
jsonschema-specifications==2024.10.1
jupyter-events==0.12.0
jupyter-lsp==2.2.5
jupyter_client==8.6.3
jupyter_core==5.7.2
jupyter_server==2.15.0
jupyter_server_terminals==0.5.3
jupyterlab==4.3.5
jupyterlab_pygments==0.3.0
jupyterlab_server==2.27.3
kiwisolver==1.4.7
langid==1.1.6
librosa==0.9.1
llvmlite==0.43.0
MarkupSafe==2.1.5
matplotlib==3.8.4
matplotlib-inline==0.1.7
mistune==3.1.1
more-itertools==10.6.0
mpmath==1.3.0
narwhals==1.25.0
nbclient==0.10.2
nbconvert==7.16.6
nbformat==5.10.4
nest-asyncio==1.6.0
networkx==3.2.1
notebook==7.3.2
notebook_shim==0.2.4
numba==0.60.0
numpy==1.22.0
nvidia-cublas-cu12==12.4.5.8
nvidia-cuda-cupti-cu12==12.4.127
nvidia-cuda-nvrtc-cu12==12.4.127
nvidia-cuda-runtime-cu12==12.4.127
nvidia-cudnn-cu12==9.1.0.70
nvidia-cufft-cu12==11.2.1.3
nvidia-curand-cu12==10.3.5.147
nvidia-cusolver-cu12==11.6.1.9
nvidia-cusparse-cu12==12.3.1.170
nvidia-cusparselt-cu12==0.6.2
nvidia-nccl-cu12==2.21.5
nvidia-nvjitlink-cu12==12.4.127
nvidia-nvtx-cu12==12.4.127
onnxruntime==1.19.2
openai==1.61.0
openai-whisper==20240930
orjson==3.10.15
overrides==7.7.0
packaging==24.2
pandas==2.0.3
pandocfilters==1.5.1
parso==0.8.4
pexpect==4.9.0
pillow==10.4.0
platformdirs==4.3.6
pooch==1.8.2
proces==0.1.7
prometheus_client==0.21.1
prompt_toolkit==3.0.50
protobuf==5.29.3
psutil==6.1.1
ptyprocess==0.7.0
pure_eval==0.2.3
pycparser==2.22
pydantic==2.10.6
pydantic_core==2.27.2
pydub==0.25.1
Pygments==2.19.1
pyparsing==3.2.1
pypinyin==0.50.0
python-dateutil==2.9.0.post0
python-dotenv==1.0.1
python-json-logger==3.2.1
python-multipart==0.0.20
pytz==2025.1
PyYAML==6.0.2
pyzmq==26.2.1
referencing==0.36.2
regex==2024.11.6
requests==2.32.3
resampy==0.4.3
rfc3339-validator==0.1.4
rfc3986-validator==0.1.1
rpds-py==0.22.3
scikit-learn==1.6.1
scipy==1.11.4
semantic-version==2.10.0
Send2Trash==1.8.3
six==1.17.0
sniffio==1.3.1
soundfile==0.13.1
soupsieve==2.6
stack-data==0.6.3
starlette==0.45.3
sympy==1.13.1
terminado==0.18.1
threadpoolctl==3.5.0
tiktoken==0.8.0
tinycss2==1.4.0
tokenizers==0.14.1
tomli==2.2.1
torch==2.6.0
torchaudio==2.6.0
tornado==6.4.2
tqdm==4.67.1
traitlets==5.14.3
triton==3.2.0
types-python-dateutil==2.9.0.20241206
typing_extensions==4.12.2
tzdata==2025.1
Unidecode==1.3.7
uri-template==1.3.0
urllib3==2.3.0
uvicorn==0.34.0
wavmark==0.0.3
wcwidth==0.2.13
webcolors==24.11.1
webencodings==0.5.1
websocket-client==1.8.0
websockets==11.0.3
Werkzeug==3.1.3
whisper-timestamped==1.14.2
zipp==3.21.0
'''



ORIGINAL_DEPENDENCIES = '''
librosa==0.9.1
faster-whisper==0.9.0
pydub==0.25.1
wavmark==0.0.3
numpy==1.22.0
eng_to_ipa==0.0.2
inflect==7.0.0
unidecode==1.3.7
whisper-timestamped==1.14.2
openai
python-dotenv
pypinyin==0.50.0
cn2an==0.5.22
jieba==0.42.1
gradio==3.48.0
langid==1.1.6
flask
notebook

'''