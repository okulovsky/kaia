from .settings import WhisperSettings
from ..docker_based import DockerBasedInstaller, DockerBasedInstallerEndpoint
from .....infra.deployment import DockerRun, SmallContainerBuilder
from .....infra import Loc
from kaia.brainbox.deciders.api.whisper import WhisperAPI
from unittest import TestCase
from pathlib import Path


class WhisperInstaller(DockerBasedInstaller):
    def __init__(self, settings: WhisperSettings):
        self.settings = settings
        builder = SmallContainerBuilder(settings.image_name, Path(__file__).parent/'container', DOCKERFILE, DEPENDENCIES)

        notebook_config = DockerRun(
            open_ports=[8899],
            additional_arguments=[ '--rm'],
            mount_folders={Loc.root_folder:'/repo'},
            command_line_arguments=['notebook'],
            propagate_gpu=self.settings.use_gpu
        )
        self.notebook_endpoint = DockerBasedInstallerEndpoint(self, notebook_config)

        server_config = DockerRun(
            mapped_ports={8084:self.settings.port},
            additional_arguments=['--rm'],
            mount_folders={self.settings.data_folder:'/data'},
            propagate_gpu=self.settings.use_gpu,
            daemon=True
        )

        self.server_endpoint = DockerBasedInstallerEndpoint(self, server_config, 15, self.settings.port, self.settings.address)

        super().__init__(builder)


    def create_api(self):
        return WhisperAPI(f'{self.settings.address}:{self.settings.port}')


    def install(self):
        self.build()
        if len(self.settings.models_to_download)>0:
            self.server_endpoint.run()
            for model in self.settings.models_to_download:
                self.create_api().load_model(model)
            self.server_endpoint.kill()

    def self_test(self, tc: TestCase):
        self.server_endpoint.run()
        for model in self.settings.models_to_download:
            self.create_api().load_model(model)
            result = self.create_api().transcribe(Path(__file__).parent/'test_voice.wav')
            tc.assertEqual(
                'One little spark and before you know it, the whole world is burning.',
                result['text'].strip()
            )
        self.server_endpoint.kill()

    def get_service_endpoint(self) -> DockerBasedInstallerEndpoint:
        return self.server_endpoint



DOCKERFILE='''
FROM python:3.9

RUN pip install {dependencies}

RUN apt-get update

RUN apt-get install ffmpeg -y

COPY . /STT/kaia

ENTRYPOINT ["python3","/STT/kaia/main.py"]

'''



DEPENDENCIES='''
anyio==4.3.0
argon2-cffi==23.1.0
argon2-cffi-bindings==21.2.0
arrow==1.3.0
asttokens==2.4.1
async-lru==2.0.4
attrs==23.2.0
Babel==2.14.0
beautifulsoup4==4.12.3
bleach==6.1.0
blinker==1.7.0
certifi==2024.2.2
cffi==1.16.0
charset-normalizer==3.3.2
click==8.1.7
colorama==0.4.6
comm==0.2.2
debugpy==1.8.1
decorator==5.1.1
defusedxml==0.7.1
exceptiongroup==1.2.0
executing==2.0.1
fastjsonschema==2.19.1
filelock==3.13.4
Flask==3.0.3
fqdn==1.5.1
fsspec==2024.3.1
h11==0.14.0
httpcore==1.0.5
httpx==0.27.0
idna==3.7
importlib_metadata==7.1.0
ipykernel==6.29.4
ipython==8.18.1
isoduration==20.11.0
itsdangerous==2.1.2
jedi==0.19.1
Jinja2==3.1.3
json5==0.9.25
jsonpointer==2.4
jsonschema==4.21.1
jsonschema-specifications==2023.12.1
jupyter-events==0.10.0
jupyter-lsp==2.2.5
jupyter_client==8.6.1
jupyter_core==5.7.2
jupyter_server==2.14.0
jupyter_server_terminals==0.5.3
jupyterlab==4.1.6
jupyterlab_pygments==0.3.0
jupyterlab_server==2.26.0
llvmlite==0.42.0
MarkupSafe==2.1.5
matplotlib-inline==0.1.6
mistune==3.0.2
more-itertools==10.2.0
mpmath==1.3.0
nbclient==0.10.0
nbconvert==7.16.3
nbformat==5.10.4
nest-asyncio==1.6.0
networkx==3.2.1
notebook==7.1.2
notebook_shim==0.2.4
numba==0.59.1
numpy==1.26.4
openai-whisper==20231117
overrides==7.7.0
packaging==24.0
pandocfilters==1.5.1
parso==0.8.4
platformdirs==4.2.0
prometheus_client==0.20.0
prompt-toolkit==3.0.43
psutil==5.9.8
pure-eval==0.2.2
pycparser==2.22
Pygments==2.17.2
python-dateutil==2.9.0.post0
python-json-logger==2.0.7
PyYAML==6.0.1
pyzmq==26.0.0
referencing==0.34.0
regex==2023.12.25
requests==2.31.0
rfc3339-validator==0.1.4
rfc3986-validator==0.1.1
rpds-py==0.18.0
Send2Trash==1.8.3
six==1.16.0
sniffio==1.3.1
soupsieve==2.5
stack-data==0.6.3
sympy==1.12
terminado==0.18.1
tiktoken==0.6.0
tinycss2==1.2.1
tomli==2.0.1
torch==2.2.2
tornado==6.4
tqdm==4.66.2
traitlets==5.14.2
types-python-dateutil==2.9.0.20240316
typing_extensions==4.11.0
uri-template==1.3.0
urllib3==2.2.1
wcwidth==0.2.13
webcolors==1.13
webencodings==0.5.1
websocket-client==1.7.0
Werkzeug==3.0.2
zipp==3.18.1
'''