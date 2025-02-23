from typing import Iterable
from unittest import TestCase
from ....framework import (
    RunConfiguration, TestReport, SmallImageBuilder, IImageBuilder, DockerWebServiceController,
    BrainBoxApi, BrainBoxTask, FileIO, INotebookableController, IModelDownloadingController, DownloadableModel
)
from .settings import ZonosSettings
from pathlib import Path


class ZonosController(
    DockerWebServiceController[ZonosSettings],
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
                'pretrained': '/home/app/.cache/huggingface'
            }
        )

    def get_notebook_configuration(self) -> RunConfiguration|None:
        return self.get_service_run_configuration(None).as_notebook_service()

    def get_default_settings(self):
        return ZonosSettings()

    def create_api(self):
        from .api import Zonos
        return Zonos()

    def _self_test_internal(self, api: BrainBoxApi, tc: TestCase) -> Iterable:
        from .api import Zonos

        api.execute(BrainBoxTask.call(Zonos).echo('argument'))


        yield (
            TestReport
            .last_call(api)
            .href('echo')
            .with_comment("Returns JSON with passed arguments and `success` fields")
        )



DOCKERFILE = f'''
FROM python:3.10

{SmallImageBuilder.APT_INSTALL('espeak-ng')}

{{{SmallImageBuilder.ADD_USER_PLACEHOLDER}}}

{{{SmallImageBuilder.PIP_INSTALL_PLACEHOLDER}}}

WORKDIR /home/app

{SmallImageBuilder.GIT_CLONE_AND_RESET(
    'https://github.com/Zyphra/Zonos/',
    'Zonos',
    'a09ff4fa50cfa66bf79986e19c191f85f5cb53e8',
    install=True
)}

COPY . /home/app/

ENTRYPOINT ["python3","/home/app/main.py"]
'''

DEPENDENCIES = '''
aiofiles==23.2.1
annotated-types==0.7.0
anyio==4.8.0
argon2-cffi==23.1.0
argon2-cffi-bindings==21.2.0
arrow==1.3.0
asttokens==3.0.0
async-lru==2.0.4
attrs==25.1.0
babel==2.17.0
beautifulsoup4==4.13.3
bleach==6.2.0
blinker==1.9.0
certifi==2025.1.31
cffi==1.17.1
charset-normalizer==3.4.1
click==8.1.8
colorama==0.4.6
comm==0.2.2
csvw==3.5.1
debugpy==1.8.12
decorator==5.2.0
defusedxml==0.7.1
dlinfo==2.0.0
exceptiongroup==1.2.2
executing==2.2.0
fastapi==0.115.8
fastjsonschema==2.21.1
ffmpy==0.5.0
filelock==3.17.0
Flask==3.1.0
fqdn==1.5.1
fsspec==2025.2.0
gradio==5.17.1
gradio_client==1.7.1
h11==0.14.0
httpcore==1.0.7
httpx==0.28.1
huggingface-hub==0.29.1
idna==3.10
inflect==7.5.0
ipykernel==6.29.5
ipython==8.32.0
ipywidgets==8.1.5
isodate==0.7.2
isoduration==20.11.0
itsdangerous==2.2.0
jedi==0.19.2
Jinja2==3.1.5
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
jupyterlab_widgets==3.0.13
kanjize==1.6.0
language-tags==1.2.0
markdown-it-py==3.0.0
MarkupSafe==2.1.5
matplotlib-inline==0.1.7
mdurl==0.1.2
mistune==3.1.2
more-itertools==10.6.0
mpmath==1.3.0
nbclient==0.10.2
nbconvert==7.16.6
nbformat==5.10.4
nest-asyncio==1.6.0
networkx==3.4.2
notebook==7.3.2
notebook_shim==0.2.4
numpy==2.2.3
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
orjson==3.10.15
overrides==7.7.0
packaging==24.2
pandas==2.2.3
pandocfilters==1.5.1
parso==0.8.4
pexpect==4.9.0
phonemizer==3.3.0
pillow==11.1.0
platformdirs==4.3.6
prometheus_client==0.21.1
prompt_toolkit==3.0.50
psutil==7.0.0
ptyprocess==0.7.0
pure_eval==0.2.3
pycparser==2.22
pydantic==2.10.6
pydantic_core==2.27.2
pydub==0.25.1
Pygments==2.19.1
pyparsing==3.2.1
python-dateutil==2.9.0.post0
python-json-logger==3.2.1
python-multipart==0.0.20
pytz==2025.1
PyYAML==6.0.2
pyzmq==26.2.1
rdflib==7.1.3
referencing==0.36.2
regex==2024.11.6
requests==2.32.3
rfc3339-validator==0.1.4
rfc3986==1.5.0
rfc3986-validator==0.1.1
rich==13.9.4
rpds-py==0.23.1
ruff==0.9.7
safehttpx==0.1.6
safetensors==0.5.2
segments==2.3.0
semantic-version==2.10.0
Send2Trash==1.8.3
shellingham==1.5.4
six==1.17.0
sniffio==1.3.1
soundfile==0.13.1
soupsieve==2.6
stack-data==0.6.3
starlette==0.45.3
SudachiDict-full==20250129
SudachiPy==0.6.10
sympy==1.13.1
terminado==0.18.1
tinycss2==1.4.0
tokenizers==0.21.0
tomli==2.2.1
tomlkit==0.13.2
torch==2.6.0
torchaudio==2.6.0
tornado==6.4.2
tqdm==4.67.1
traitlets==5.14.3
transformers==4.49.0
triton==3.2.0
typeguard==4.4.2
typer==0.15.1
types-python-dateutil==2.9.0.20241206
typing_extensions==4.12.2
tzdata==2025.1
uri-template==1.3.0
uritemplate==4.1.1
urllib3==2.3.0
uv==0.6.2
uvicorn==0.34.0
wcwidth==0.2.13
webcolors==24.11.1
webencodings==0.5.1
websocket-client==1.8.0
websockets==14.2
Werkzeug==3.1.3
widgetsnbextension==4.0.13
'''

