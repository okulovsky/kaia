from unittest import TestCase
from ..arch import LocalImageInstaller, DockerService, BrainBoxServiceRunner
from ..arch.utils import check_if_its_sound
from kaia.brainbox.deployment import SmallImageBuilder
from ...core import BrainBoxApi, BrainBoxTask, IntegrationTestResult, OneModelWarmuper
from .settings import CoquiTTSSettings
from .api import CoquiTTS, CoquiTTSExtendedAPI
from pathlib import Path



class CoquiTTSInstaller(LocalImageInstaller):
    def __init__(self, settings: CoquiTTSSettings):
        self.settings = settings
        self.model_info = None
        service = DockerService(
            self, self.settings.port, self.settings.startup_time_in_seconds,
            BrainBoxServiceRunner(
                publish_ports={self.settings.port: 8084},
                gpu_required=BrainBoxServiceRunner.GpuRequirement.Preffered,
                command_line_arguments=() if self.settings.autoload_model is None else ['--autoload', self.settings.autoload_model]
            )
        )

        super().__init__(
            'coqui-tts',
            Path(__file__).parent / 'container',
            DOCKERFILE,
            DEPENDENCIES,
            service
        )

        self.notebook_service = self.main_service.as_notebook_service()
        self.warmuper = OneModelWarmuper()

    def install_model_endpoint(self, model_name, mode) -> DockerService:
        return self.main_service.as_service_worker('--install', model_name, '--install-mode', mode)

    def post_install(self):
        for model in self.settings.builtin_models_to_download:
            if not self.executor.is_dir(self.resource_folder('builtin')/model.due_folder_name):
                self.install_model_endpoint(model.model_name, model.mode).run()

    def create_api(self) -> CoquiTTSExtendedAPI:
        return CoquiTTSExtendedAPI(f'{self.ip_address}:{self.settings.port}')

    def export_model_from_training(
            self,
            source_model_file_path: Path,
            model_name: str):
        target_model_file_path = str(self.resource_folder('custom')/'{model_name}.pth')
        self.executor.upload_file(source_model_file_path, target_model_file_path)
        self.executor.upload_file(source_model_file_path.parent / 'config.json', target_model_file_path + '.json')
        self.executor.upload_file(
            source_model_file_path.parent.parent.parent / 'data/speakers.pth',
            str(target_model_file_path) + '.speakers.pth'
        )
        return f'custom_models/{model_name}.pth'

    def upload_voice(self, file: Path):
        self.executor.upload_file(file, self.resource_folder('voices')/file.name)

    def _brainbox_self_test_internal(self, api: BrainBoxApi, tc: TestCase):
        self.upload_voice(Path(__file__).parent/'test_voice.wav')
        for model in self.settings.builtin_models_to_download:
            yield IntegrationTestResult(0, f"Model {model.model_name}")
            if model.test_dub:
                yield IntegrationTestResult(1, f"Voiceover", None)
                text = IntegrationTestResult.VOICEOVER_SAMPLE
                yield IntegrationTestResult(2, None, text)
                content = api.pull_content(api.execute(
                    BrainBoxTask.call(CoquiTTS).dub(text = text).to_task(model.model_name)
                ))
                check_if_its_sound(content, tc)
                yield IntegrationTestResult(2, None, content)


            if model.test_voice_clone:
                yield IntegrationTestResult(1, f"Voice clone", None)
                text = IntegrationTestResult.VOICEOVER_SAMPLE
                yield IntegrationTestResult(2, None, text)
                content = api.pull_content(api.execute(
                    BrainBoxTask.call(CoquiTTS).voice_clone(text = text, voice = 'test_voice').to_task(model.model_name)
                ))
                check_if_its_sound(content, tc)
                yield IntegrationTestResult(2, None, content)



    def warmup(self, parameters: str):
        self.run_if_not_running_and_wait()
        self.warmuper.load_model(self, parameters)

    def create_brainbox_decider_api(self, parameters: str) -> CoquiTTS:
        model = self.warmuper.check_and_return_running_model(self, parameters)
        return CoquiTTS(f'{self.ip_address}:{self.settings.port}', model)



DOCKERFILE = f'''
FROM python:3.11

RUN apt-get update

RUN apt-get install espeak -y

{{{SmallImageBuilder.ADD_USER_PLACEHOLDER}}}

{{{SmallImageBuilder.PIP_INSTALL_PLACEHOLDER}}}

WORKDIR /home/app

RUN git clone https://github.com/coqui-ai/TTS

WORKDIR /home/app/TTS

RUN git reset --hard eef419b37393b11cc741662d041d8d793e011f2d

RUN pip install -e .[all,dev,notebooks]

COPY . /home/app/TTS/TTS/kaia

ENTRYPOINT ["python3","/home/app/TTS/TTS/kaia/main.py"]
'''

DEPENDENCIES = '''
absl-py==2.1.0
aiohttp==3.9.3
aiosignal==1.3.1
annotated-types==0.6.0
anyascii==0.3.2
anyio==4.3.0
argon2-cffi==23.1.0
argon2-cffi-bindings==21.2.0
arrow==1.3.0
astroid==2.7.3
asttokens==2.4.1
async-lru==2.0.4
attrs==23.2.0
audioread==3.0.1
Babel==2.14.0
bangla==0.0.2
beautifulsoup4==4.12.3
black==24.2.0
bleach==6.1.0
blinker==1.7.0
blis==0.7.11
bnnumerizer==0.0.2
bnunicodenormalizer==0.1.6
bokeh==1.4.0
catalogue==2.0.10
certifi==2024.2.2
cffi==1.16.0
charset-normalizer==3.3.2
click==8.1.7
cloudpathlib==0.16.0
comm==0.2.2
confection==0.1.4
contourpy==1.2.0
coqpit==0.0.17
coverage==7.4.3
cutlet==0.3.0
cycler==0.12.1
cymem==2.0.8
Cython==3.0.9
dateparser==1.1.8
debugpy==1.8.1
decorator==5.1.1
defusedxml==0.7.1
docopt==0.6.2
einops==0.7.0
encodec==0.1.1
executing==2.0.1
fastjsonschema==2.19.1
filelock==3.13.1
Flask==3.0.2
fonttools==4.49.0
fqdn==1.5.1
frozenlist==1.4.1
fsspec==2024.2.0
fugashi==1.3.1
g2pkk==0.1.2
grpcio==1.62.1
gruut==2.2.3
gruut-ipa==0.13.0
gruut-lang-de==2.0.0
gruut-lang-en==2.0.0
gruut-lang-es==2.0.0
gruut-lang-fr==2.0.2
h11==0.14.0
hangul-romanize==0.1.0
httpcore==1.0.4
httpx==0.27.0
huggingface-hub==0.21.4
idna==3.6
inflect==7.0.0
ipykernel==6.29.3
ipython==8.22.2
isoduration==20.11.0
isort==5.13.2
itsdangerous==2.1.2
jaconv==0.3.4
jamo==0.4.1
jedi==0.19.1
jieba==0.42.1
Jinja2==3.1.3
joblib==1.3.2
json5==0.9.24
jsonlines==1.2.0
jsonpointer==2.4
jsonschema==4.21.1
jsonschema-specifications==2023.12.1
jupyter-events==0.10.0
jupyter-lsp==2.2.4
jupyter_client==8.6.1
jupyter_core==5.7.2
jupyter_server==2.13.0
jupyter_server_terminals==0.5.3
jupyterlab==4.1.5
jupyterlab_pygments==0.3.0
jupyterlab_server==2.25.4
kiwisolver==1.4.5
langcodes==3.3.0
lazy-object-proxy==1.10.0
lazy_loader==0.3
librosa==0.10.1
llvmlite==0.42.0
Markdown==3.5.2
MarkupSafe==2.1.5
matplotlib==3.8.3
matplotlib-inline==0.1.6
mccabe==0.6.1
mecab-python3==1.0.6
mistune==3.0.2
mojimoji==0.0.13
mpmath==1.3.0
msgpack==1.0.8
multidict==6.0.5
murmurhash==1.0.10
mypy-extensions==1.0.0
nbclient==0.10.0
nbconvert==7.16.3
nbformat==5.10.3
nest-asyncio==1.6.0
networkx==2.8.8
nltk==3.8.1
nose2==0.14.1
notebook==7.1.2
notebook_shim==0.2.4
num2words==0.5.13
numba==0.59.0
numpy==1.26.4
nvidia-cublas-cu12==12.1.3.1
nvidia-cuda-cupti-cu12==12.1.105
nvidia-cuda-nvrtc-cu12==12.1.105
nvidia-cuda-runtime-cu12==12.1.105
nvidia-cudnn-cu12==8.9.2.26
nvidia-cufft-cu12==11.0.2.54
nvidia-curand-cu12==10.3.2.106
nvidia-cusolver-cu12==11.4.5.107
nvidia-cusparse-cu12==12.1.0.106
nvidia-nccl-cu12==2.19.3
nvidia-nvjitlink-cu12==12.4.99
nvidia-nvtx-cu12==12.1.105
overrides==7.7.0
packaging==24.0
pandas==1.5.3
pandocfilters==1.5.1
parso==0.8.3
pathspec==0.12.1
pexpect==4.9.0
pillow==10.2.0
platformdirs==4.2.0
pooch==1.8.1
preshed==3.0.9
prometheus_client==0.20.0
prompt-toolkit==3.0.43
protobuf==4.25.3
psutil==5.9.8
ptyprocess==0.7.0
pure-eval==0.2.2
pycparser==2.21
pydantic==2.6.3
pydantic_core==2.16.3
Pygments==2.17.2
pylint==2.10.2
pynndescent==0.5.11
pyparsing==3.1.2
pypinyin==0.51.0
pysbd==0.3.4
python-crfsuite==0.9.10
python-dateutil==2.9.0.post0
python-json-logger==2.0.7
pytz==2024.1
PyYAML==6.0.1
pyzmq==25.1.2
referencing==0.34.0
regex==2023.12.25
requests==2.31.0
rfc3339-validator==0.1.4
rfc3986-validator==0.1.1
rpds-py==0.18.0
safetensors==0.4.2
scikit-learn==1.4.1.post1
scipy==1.12.0
Send2Trash==1.8.2
six==1.16.0
smart-open==6.4.0
sniffio==1.3.1
soundfile==0.12.1
soupsieve==2.5
soxr==0.3.7
spacy==3.7.4
spacy-loggers==1.0.5
srsly==2.4.8
stack-data==0.6.3
SudachiDict-core==20240109
SudachiPy==0.6.8
sympy==1.12
tensorboard==2.16.2
tensorboard-data-server==0.7.2
terminado==0.18.1
thinc==8.2.3
threadpoolctl==3.3.0
tinycss2==1.2.1
tokenizers==0.15.2
toml==0.10.2
torch==2.2.1
torchaudio==2.2.1
tornado==6.4
tqdm==4.66.2
trainer==0.0.36
traitlets==5.14.2
transformers==4.38.2
triton==2.2.0
typer==0.9.0
types-python-dateutil==2.9.0.20240316
typing_extensions==4.10.0
tzlocal==5.2
umap-learn==0.5.5
Unidecode==1.3.8
unidic-lite==1.0.8
uri-template==1.3.0
urllib3==2.2.1
wasabi==1.1.2
wcwidth==0.2.13
weasel==0.3.4
webcolors==1.13
webencodings==0.5.1
websocket-client==1.7.0
Werkzeug==3.0.1
wrapt==1.12.1
yarl==1.9.4
'''