from typing import Iterable
from unittest import TestCase
from ....framework import (
    RunConfiguration, TestReport, SmallImageBuilder, IImageBuilder, DockerWebServiceController,
    BrainBoxApi, BrainBoxTask, FileIO, INotebookableController, IModelDownloadingController, DownloadableModel,
    File
)
from .settings import ResembleEnhanceSettings
from ...common import check_if_its_sound
from pathlib import Path


class ResembleEnhanceController(
    DockerWebServiceController[ResembleEnhanceSettings],
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
                'uploads' : '/uploads',
                'outputs' : '/outputs',
                'models' : '/home/app/.local/lib/python3.11/site-packages/resemble_enhance/model_repo'
            },
        )

    def get_notebook_configuration(self) -> RunConfiguration|None:
        return self.get_service_run_configuration(None).as_notebook_service()



    def get_default_settings(self):
        return ResembleEnhanceSettings()

    def create_api(self):
        from .api import ResembleEnhance
        return ResembleEnhance()

    def _self_test_internal(self, api: BrainBoxApi, tc: TestCase) -> Iterable:
        from .api import ResembleEnhance

        input = File.read(Path(__file__).parent/'sample_10db.wav')
        result = api.execute(BrainBoxTask.call(ResembleEnhance).process(input))
        for file in result:
            check_if_its_sound(api.open_file(file).content, tc)

        yield (
            TestReport
            .last_call(api)
            .href('10db')
            .result_is_array_of_files(File.Kind.Audio)
        )


DOCKERFILE = f"""
FROM python:3.11.11

{SmallImageBuilder.APT_INSTALL('git-lfs')}

{{{SmallImageBuilder.ADD_USER_PLACEHOLDER}}}

{{{SmallImageBuilder.PIP_INSTALL_PLACEHOLDER}}}

WORKDIR /home/app

COPY . /home/app



ENTRYPOINT ["python3", "/home/app/main.py"]
"""


DEPENDENCIES = """
aiofiles==23.2.1
altair==5.5.0
annotated-types==0.7.0
antlr4-python3-runtime==4.9.3
anyio==4.8.0
argon2-cffi==23.1.0
argon2-cffi-bindings==21.2.0
arrow==1.3.0
asttokens==3.0.0
async-lru==2.0.4
attrs==24.3.0
audioread==3.0.1
babel==2.16.0
beautifulsoup4==4.12.3
bleach==6.2.0
blinker==1.9.0
celluloid==0.2.0
certifi==2024.12.14
cffi==1.17.1
charset-normalizer==3.4.1
click==8.1.8
comm==0.2.2
contourpy==1.3.1
cycler==0.12.1
debugpy==1.8.12
decorator==5.1.1
deepspeed==0.12.4
defusedxml==0.7.1
executing==2.2.0
fastapi==0.115.6
fastjsonschema==2.21.1
ffmpy==0.5.0
filelock==3.16.1
Flask==3.1.0
fonttools==4.55.3
fqdn==1.5.1
fsspec==2024.12.0
gradio==4.8.0
gradio_client==0.7.1
h11==0.14.0
hjson==3.1.0
httpcore==1.0.7
httpx==0.28.1
huggingface-hub==0.27.1
idna==3.10
importlib_resources==6.5.2
ipykernel==6.29.5
ipython==8.31.0
isoduration==20.11.0
itsdangerous==2.2.0
jedi==0.19.2
Jinja2==3.1.5
joblib==1.4.2
json5==0.10.0
jsonpointer==3.0.0
jsonschema==4.23.0
jsonschema-specifications==2024.10.1
jupyter-events==0.11.0
jupyter-lsp==2.2.5
jupyter_client==8.6.3
jupyter_core==5.7.2
jupyter_server==2.15.0
jupyter_server_terminals==0.5.3
jupyterlab==4.3.4
jupyterlab_pygments==0.3.0
jupyterlab_server==2.27.3
kiwisolver==1.4.8
lazy_loader==0.4
librosa==0.10.1
llvmlite==0.43.0
markdown-it-py==3.0.0
MarkupSafe==2.1.5
matplotlib==3.8.1
matplotlib-inline==0.1.7
mdurl==0.1.2
mistune==3.1.0
mpmath==1.3.0
msgpack==1.1.0
narwhals==1.22.0
nbclient==0.10.2
nbconvert==7.16.5
nbformat==5.10.4
nest-asyncio==1.6.0
networkx==3.4.2
ninja==1.11.1.3
notebook==7.3.2
notebook_shim==0.2.4
numba==0.60.0
numpy==1.26.2
nvidia-cublas-cu12==12.1.3.1
nvidia-cuda-cupti-cu12==12.1.105
nvidia-cuda-nvrtc-cu12==12.1.105
nvidia-cuda-runtime-cu12==12.1.105
nvidia-cudnn-cu12==8.9.2.26
nvidia-cufft-cu12==11.0.2.54
nvidia-curand-cu12==10.3.2.106
nvidia-cusolver-cu12==11.4.5.107
nvidia-cusparse-cu12==12.1.0.106
nvidia-ml-py==12.560.30
nvidia-nccl-cu12==2.18.1
nvidia-nvjitlink-cu12==12.6.85
nvidia-nvtx-cu12==12.1.105
omegaconf==2.3.0
orjson==3.10.14
overrides==7.7.0
packaging==24.2
pandas==2.1.3
pandocfilters==1.5.1
parso==0.8.4
pexpect==4.9.0
pillow==10.4.0
platformdirs==4.3.6
pooch==1.8.2
prometheus_client==0.21.1
prompt_toolkit==3.0.50
psutil==6.1.1
ptflops==0.7.1.2
ptyprocess==0.7.0
pure_eval==0.2.3
py-cpuinfo==9.0.0
pycparser==2.22
pydantic==2.10.5
pydantic_core==2.27.2
pydub==0.25.1
Pygments==2.19.1
pynvml==12.0.0
pyparsing==3.2.1
python-dateutil==2.9.0.post0
python-json-logger==3.2.1
python-multipart==0.0.20
pytz==2024.2
PyYAML==6.0.2
pyzmq==26.2.0
referencing==0.36.1
requests==2.32.3
resampy==0.4.2
resemble-enhance==0.0.1
rfc3339-validator==0.1.4
rfc3986-validator==0.1.1
rich==13.7.0
rpds-py==0.22.3
scikit-learn==1.6.1
scipy==1.11.4
semantic-version==2.10.0
Send2Trash==1.8.3
shellingham==1.5.4
six==1.17.0
sniffio==1.3.1
soundfile==0.12.1
soupsieve==2.6
soxr==0.5.0.post1
stack-data==0.6.3
starlette==0.41.3
sympy==1.13.3
tabulate==0.8.10
terminado==0.18.1
threadpoolctl==3.5.0
tinycss2==1.4.0
tomlkit==0.12.0
torch==2.1.1
torchaudio==2.1.1
torchvision==0.16.1
tornado==6.4.2
tqdm==4.66.1
traitlets==5.14.3
triton==2.1.0
typer==0.15.1
types-python-dateutil==2.9.0.20241206
typing_extensions==4.12.2
tzdata==2024.2
uri-template==1.3.0
urllib3==2.3.0
uvicorn==0.34.0
wcwidth==0.2.13
webcolors==24.11.1
webencodings==0.5.1
websocket-client==1.8.0
websockets==11.0.3
Werkzeug==3.1.3
"""

ORIGINAL_DEPENDENCIES = '''
resemble-enhance
'''