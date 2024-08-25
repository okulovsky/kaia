from pathlib import Path
from .settings import ResemblyzerSettings
from ..arch import LocalImageInstaller, DockerService, BrainBoxServiceRunner
from ...deployment import SmallImageBuilder
from .api import Resemblyzer, ResemblyzerExtendedApi
from unittest import TestCase
from kaia.brainbox.media_library import MediaLibrary
from ...core import BrainBoxApi, BrainBoxTask, IntegrationTestResult, File, BrainBoxTaskPack
from ..collector import Collector

class ResemblyzerInstaller(LocalImageInstaller):
    def __init__(self, settings: ResemblyzerSettings):
        self.settings = settings


        service = DockerService(
            self, self.settings.port, self.settings.startup_time_in_seconds,
            BrainBoxServiceRunner(
                publish_ports={self.settings.port: 8084}
            )
        )

        super().__init__(
            'resemblyzer',
            Path(__file__).parent / 'container',
            DOCKERFILE,
            DEPENDENCIES,
            service)

        self.notebook_service = service.as_notebook_service()

    def create_api(self) -> ResemblyzerExtendedApi:
        return ResemblyzerExtendedApi(f'{self.ip_address}:{self.settings.port}')

    def _brainbox_self_test_internal(self, api: BrainBoxApi, tc: TestCase):
        self.run_if_not_running_and_wait()
        full_api = self.create_api()
        full_api.delete_dataset('test_dataset')
        ml = MediaLibrary.read(Path(__file__).parent/'test_media_library.zip')
        full_api.upload_dataset('test_dataset', ml)
        stats = full_api.train('test_dataset')
        print(stats)
        tc.assertGreater(stats['accuracy'], 0.9)
        self.kill()

        builder = Collector.PackBuilder()
        contents = {}
        speakers = []
        for record in ml.records:
            if record.tags['split'] == 'test':
                if record.tags['speaker'] not in speakers:
                    speakers.append(record.tags['speaker'])
                contents[record.filename] = File(f'sample', record.get_content(), File.Kind.Audio)
                builder.append(
                    BrainBoxTask.call(Resemblyzer)(file=contents[record.filename]).to_task('test_dataset'),
                    dict(record_id=record.filename)
                )
        result = api.execute(builder.to_collector_pack('to_array'))

        for speaker in speakers:
            yield IntegrationTestResult(0, f"Speaker {speaker}")
            for r in result:
                if r['result'] != speaker:
                    continue
                yield IntegrationTestResult(0, None, contents[r['tags']['record_id']])







    def create_brainbox_decider_api(self, parameters: str) -> Resemblyzer:
        return Resemblyzer(f'{self.ip_address}:{self.settings.port}', parameters)




DOCKERFILE = f'''
FROM python:3.8

{{{SmallImageBuilder.ADD_USER_PLACEHOLDER}}}

{{{SmallImageBuilder.PIP_INSTALL_PLACEHOLDER}}}

RUN pip freeze

COPY . /home/app/kaia

ENTRYPOINT ["python3","/home/app/kaia/main.py"]
'''

DEPENDENCIES = '''
anyio==4.4.0
argon2-cffi==23.1.0
argon2-cffi-bindings==21.2.0
arrow==1.3.0
asttokens==2.4.1
async-lru==2.0.4
attrs==23.2.0
audioread==3.0.1
Babel==2.15.0
backcall==0.2.0
beautifulsoup4==4.12.3
bleach==6.1.0
blinker==1.8.2
certifi==2024.7.4
cffi==1.16.0
charset-normalizer==3.3.2
click==8.1.7
comm==0.2.2
contourpy==1.1.1
cycler==0.12.1
debugpy==1.8.2
decorator==5.1.1
defusedxml==0.7.1
exceptiongroup==1.2.1
executing==2.0.1
fastjsonschema==2.20.0
filelock==3.15.4
Flask==3.0.3
fonttools==4.53.1
fqdn==1.5.1
fsspec==2024.6.1
h11==0.14.0
httpcore==1.0.5
httpx==0.27.0
idna==3.7
importlib_metadata==8.0.0
importlib_resources==6.4.0
ipykernel==6.29.5
ipython==8.12.3
isoduration==20.11.0
itsdangerous==2.2.0
jedi==0.19.1
Jinja2==3.1.4
joblib==1.4.2
json5==0.9.25
jsonpointer==3.0.0
jsonschema==4.22.0
jsonschema-specifications==2023.12.1
jupyter-events==0.10.0
jupyter-lsp==2.2.5
jupyter_client==8.6.2
jupyter_core==5.7.2
jupyter_server==2.14.1
jupyter_server_terminals==0.5.3
jupyterlab==4.2.3
jupyterlab_pygments==0.3.0
jupyterlab_server==2.27.2
kiwisolver==1.4.5
lazy_loader==0.4
librosa==0.10.2.post1
llvmlite==0.41.1
MarkupSafe==2.1.5
matplotlib==3.7.5
matplotlib-inline==0.1.7
mistune==3.0.2
mpmath==1.3.0
msgpack==1.0.8
nbclient==0.10.0
nbconvert==7.16.4
nbformat==5.10.4
nest-asyncio==1.6.0
networkx==3.1
notebook==7.2.1
notebook_shim==0.2.4
numba==0.58.1
numpy==1.24.4
nvidia-cublas-cu12==12.1.3.1
nvidia-cuda-cupti-cu12==12.1.105
nvidia-cuda-nvrtc-cu12==12.1.105
nvidia-cuda-runtime-cu12==12.1.105
nvidia-cudnn-cu12==8.9.2.26
nvidia-cufft-cu12==11.0.2.54
nvidia-curand-cu12==10.3.2.106
nvidia-cusolver-cu12==11.4.5.107
nvidia-cusparse-cu12==12.1.0.106
nvidia-nccl-cu12==2.20.5
nvidia-nvjitlink-cu12==12.5.82
nvidia-nvtx-cu12==12.1.105
overrides==7.7.0
packaging==24.1
pandas==2.0.3
pandocfilters==1.5.1
parso==0.8.4
pexpect==4.9.0
pickleshare==0.7.5
pillow==10.4.0
pkgutil_resolve_name==1.3.10
platformdirs==4.2.2
pooch==1.8.2
prometheus_client==0.20.0
prompt_toolkit==3.0.47
psutil==6.0.0
ptyprocess==0.7.0
pure-eval==0.2.2
pycparser==2.22
Pygments==2.18.0
pyparsing==3.1.2
python-dateutil==2.9.0.post0
python-json-logger==2.0.7
pytz==2024.1
PyYAML==6.0.1
pyzmq==26.0.3
referencing==0.35.1
requests==2.32.3
Resemblyzer==0.1.4
rfc3339-validator==0.1.4
rfc3986-validator==0.1.1
rpds-py==0.19.0
scikit-learn==1.3.2
scipy==1.10.1
Send2Trash==1.8.3
six==1.16.0
sniffio==1.3.1
soundfile==0.12.1
soupsieve==2.5
soxr==0.3.7
stack-data==0.6.3
sympy==1.12.1
terminado==0.18.1
threadpoolctl==3.5.0
tinycss2==1.3.0
tomli==2.0.1
torch==2.3.1
tornado==6.4.1
tqdm==4.66.4
traitlets==5.14.3
triton==2.3.1
types-python-dateutil==2.9.0.20240316
typing==3.7.4.3
typing_extensions==4.12.2
tzdata==2024.1
uri-template==1.3.0
urllib3==2.2.2
wcwidth==0.2.13
webcolors==24.6.0
webencodings==0.5.1
webrtcvad==2.0.10
websocket-client==1.8.0
Werkzeug==3.0.3
zipp==3.19.2
'''