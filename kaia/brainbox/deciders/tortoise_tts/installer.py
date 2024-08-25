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
                    voices = '/home/app/tortoise-tts/tortoise/voices',
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
            DEPENDENCIES,
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
        self.install_service.run()



DOCKERFILE = f'''
FROM python:3.8

{{{SmallImageBuilder.ADD_USER_PLACEHOLDER}}}

{{{SmallImageBuilder.PIP_INSTALL_PLACEHOLDER}}}

WORKDIR /home/app

RUN git clone https://github.com/neonbjb/tortoise-tts

WORKDIR /home/app/tortoise-tts

RUN git reset --hard 3c4d9c51316cd2421cc2dea11ac3a7a2d3394acd

RUN pip install -e .

COPY . /home/app/kaia/

ENTRYPOINT ["python3","/home/app/kaia/main.py"]
'''




DEPENDENCIES = '''
annotated-types==0.5.0
anyio==3.7.1
appdirs==1.4.4
argon2-cffi==21.3.0
argon2-cffi-bindings==21.2.0
arrow==1.2.3
asttokens==2.2.1
async-lru==2.0.4
attrs==23.1.0
audioread==3.0.0
Babel==2.12.1
backcall==0.2.0
beautifulsoup4==4.12.2
bleach==6.0.0
blinker==1.6.2
certifi==2022.12.7
cffi==1.15.1
charset-normalizer==2.1.1
click==8.1.6
colorama==0.4.6
comm==0.1.4
debugpy==1.6.7
decorator==5.1.1
defusedxml==0.7.1
einops==0.6.1
exceptiongroup==1.1.2
executing==1.2.0
fastjsonschema==2.18.0
filelock==3.9.0
Flask==2.3.2
fqdn==1.5.1
fsspec==2023.6.0
huggingface-hub==0.16.4
idna==3.4
importlib-metadata==6.8.0
importlib-resources==6.0.1
inflect==7.0.0
ipykernel==6.25.1
ipython==8.12.2
isoduration==20.11.0
itsdangerous==2.1.2
jedi==0.19.0
Jinja2==3.1.2
joblib==1.3.1
json5==0.9.14
jsonpointer==2.4
jsonschema==4.19.0
jsonschema-specifications==2023.7.1
jupyter-events==0.7.0
jupyter-lsp==2.2.0
jupyter_client==8.3.0
jupyter_core==5.3.1
jupyter_server==2.7.0
jupyter_server_terminals==0.4.4
jupyterlab==4.0.4
jupyterlab-pygments==0.2.2
jupyterlab_server==2.24.0
lazy_loader==0.3
librosa==0.10.0.post2
llvmlite==0.40.1
MarkupSafe==2.1.2
matplotlib-inline==0.1.6
mistune==3.0.1
mpmath==1.2.1
msgpack==1.0.5
nbclient==0.8.0
nbconvert==7.7.3
nbformat==5.9.2
nest-asyncio==1.5.7
networkx==3.0
notebook==7.0.2
notebook_shim==0.2.3
numba==0.57.1
numpy==1.24.1
overrides==7.4.0
packaging==23.1
pandocfilters==1.5.0
parso==0.8.3
pickleshare==0.7.5
Pillow==9.3.0
pkgutil_resolve_name==1.3.10
platformdirs==3.10.0
pooch==1.6.0
progressbar==2.5
prometheus-client==0.17.1
prompt-toolkit==3.0.39
psutil==5.9.5
pure-eval==0.2.2
pycparser==2.21
pydantic==2.1.1
pydantic_core==2.4.0
Pygments==2.16.1
python-dateutil==2.8.2
python-json-logger==2.0.7
pytz==2023.3
PyYAML==6.0.1
pyzmq==25.1.0
referencing==0.30.2
regex==2023.6.3
requests==2.28.1
rfc3339-validator==0.1.4
rfc3986-validator==0.1.1
rotary-embedding-torch==0.2.6
rpds-py==0.9.2
scikit-learn==1.3.0
scipy==1.10.1
Send2Trash==1.8.2
six==1.16.0
sniffio==1.3.0
soundfile==0.12.1
soupsieve==2.4.1
soxr==0.3.5
stack-data==0.6.2
sympy==1.11.1
terminado==0.17.1
threadpoolctl==3.2.0
tinycss2==1.2.1
tokenizers==0.13.3
tomli==2.0.1
torch==2.0.0
torchaudio==2.0.1
torchvision==0.15.1
tornado==6.3.2
tqdm==4.65.1
traitlets==5.9.0
transformers==4.29.2
typing_extensions==4.7.1
Unidecode==1.3.6
uri-template==1.3.0
urllib3==1.26.13
wcwidth==0.2.6
webcolors==1.13
webencodings==0.5.1
websocket-client==1.6.1
Werkzeug==2.3.6
zipp==3.16.2

'''