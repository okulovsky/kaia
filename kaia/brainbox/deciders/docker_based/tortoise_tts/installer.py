from .settings import TortoiseTTSSettings
from ..docker_based import DockerBasedInstaller, DockerBasedInstallerEndpoint
from ..utils import check_if_its_sound
from unittest import TestCase
from pathlib import Path
from kaia.infra import deployment
from kaia.brainbox.deciders.api.tortoise_tts import TortoiseTTSApi



class TortoiseTTSInstaller(DockerBasedInstaller):
    def __init__(self, settings: TortoiseTTSSettings):
        self.settings = settings

        builder = deployment.SmallContainerBuilder(
            self.settings.image_name,
            Path(__file__).parent / 'container',
            DOCKERFILE,
            DEPENDENCIES
        )

        mount = {
            self.settings.get_voice_path(): '/tortoise-tts/tortoise/voices',
            self.settings.outputs_folder: '/stash',
            self.settings.hf_models_folder: '/root/.cache/huggingface/hub/',
            self.settings.tortoise_models_folder: '/root/.cache/tortoise/models'
        }

        server_config = deployment.DockerRun(
            mount_folders=mount,
            mapped_ports={8084: self.settings.port},
            propagate_gpu=True,
            daemon=True,
        )

        install_config = deployment.DockerRun(
            mount_folders=mount,
            propagate_gpu=True,
            daemon=False,
            command_line_arguments=['install']
        )
        self.install_endpoint = DockerBasedInstallerEndpoint(self, install_config)
        self.server_endpoint = DockerBasedInstallerEndpoint(self, server_config, 45, self.settings.port)
        super().__init__(builder)

    def create_api(self):
        return TortoiseTTSApi(f'{self.settings.address}:{self.settings.port}', self.settings.outputs_folder)

    def self_test(self, tc: TestCase):
        print('Running endpoint')
        self.server_endpoint.run()
        api = self.create_api()
        print('Sending request')
        contents = api.dub_and_return_bytes('Hello, this is tortoise, tee, tee, ass.', 'test_voice')
        print('Killing endpoint')
        self.server_endpoint.kill()
        for content in contents:
            check_if_its_sound(content, tc)


    def install(self):
        self.server_endpoint.kill()
        self.build()
        self.executor.create_empty_folder(self.settings.get_voice_path(None))
        self.executor.create_empty_folder(self.settings.hf_models_folder)
        self.executor.create_empty_folder(self.settings.tortoise_models_folder)
        self.executor.create_empty_folder(self.settings.outputs_folder)
        self.executor.upload_file(Path(__file__).parent / 'test_voice.wav', self.settings.get_voice_path('test_voice')/'test_voice.wav')
        self.install_endpoint.run()

    def get_service_endpoint(self) -> DockerBasedInstallerEndpoint:
        return self.server_endpoint


DOCKERFILE = '''
FROM python:3.8

RUN pip install {dependencies}

RUN git clone https://github.com/neonbjb/tortoise-tts

WORKDIR tortoise-tts

RUN git reset --hard 3c4d9c51316cd2421cc2dea11ac3a7a2d3394acd

RUN pip install -e .

COPY . /tortoise-tts/kaia

RUN ls /tortoise-tts

ENTRYPOINT ["python3","/tortoise-tts/kaia/main.py"]
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