from typing import Iterable
from unittest import TestCase
from ....framework import (
    RunConfiguration, TestReport, SmallImageBuilder, IImageBuilder, DockerWebServiceController,
    BrainBoxApi, BrainBoxTask, FileIO, INotebookableController, LocalExecutor, File
)
from ...common import VOICEOVER_TEXT, check_if_its_sound
from .settings import CoquiTTSSettings
from pathlib import Path


class CoquiTTSController(DockerWebServiceController[CoquiTTSSettings], INotebookableController):
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
            parameter,
            publish_ports={self.connection_settings.port: 8084},
        )

    def get_notebook_configuration(self) -> RunConfiguration|None:
        return self.get_service_run_configuration(None).as_notebook_service()

    def get_default_settings(self):
        return CoquiTTSSettings()

    def create_api(self):
        from .api import CoquiTTS
        return CoquiTTS()

    def post_install(self):
        for model in self.settings.builtin_models_to_download:
            path = self.resource_folder('builtin') / model.due_folder_name
            if not path.is_dir():
                cfg = self.get_service_run_configuration(None).as_service_worker(
                    '--install',
                    model.model_name,
                    '--install-mode',
                    model.mode
                )
                self.run_auxiliary_configuration(cfg)

    def _self_test_internal(self, api: BrainBoxApi, tc: TestCase) -> Iterable:
        from .tests import Test
        yield from Test(api, tc).test_all(self.settings)






DOCKERFILE = f'''
FROM python:3.11

{SmallImageBuilder.APT_INSTALL('espeak')}

{{{SmallImageBuilder.ADD_USER_PLACEHOLDER}}}

{{{SmallImageBuilder.PIP_INSTALL_PLACEHOLDER}}}

WORKDIR /home/app

{SmallImageBuilder.GIT_CLONE_AND_RESET(
    'https://github.com/coqui-ai/TTS',
    'TTS',
    'dbf1a08a0d4e47fdad6172e433eeb34bc6b13b4e', 
    '[all,dev,notebooks]'
)}

COPY . /home/app/TTS/kaia

ENTRYPOINT ["python3","/home/app/TTS/kaia/main.py"]
'''

DEPENDENCIES = '''
absl-py==2.1.0
aiohappyeyeballs==2.4.4
aiohttp==3.11.11
aiosignal==1.3.2
annotated-types==0.7.0
anyascii==0.3.2
anyio==4.7.0
argon2-cffi==23.1.0
argon2-cffi-bindings==21.2.0
arrow==1.3.0
astroid==2.7.3
asttokens==3.0.0
async-lru==2.0.4
attrs==24.3.0
audioread==3.0.1
babel==2.16.0
bangla==0.0.2
beautifulsoup4==4.12.3
black==24.10.0
bleach==6.2.0
blinker==1.9.0
blis==1.1.0
bnnumerizer==0.0.2
bnunicodenormalizer==0.1.7
bokeh==1.4.0
catalogue==2.0.10
certifi==2024.12.14
cffi==1.17.1
charset-normalizer==3.4.0
click==8.1.7
cloudpathlib==0.20.0
comm==0.2.2
confection==0.1.5
contourpy==1.3.1
coqpit==0.0.17
coverage==7.6.9
cutlet==0.4.0
cycler==0.12.1
cymem==2.0.10
Cython==3.0.11
dateparser==1.1.8
debugpy==1.8.11
decorator==5.1.1
defusedxml==0.7.1
docopt==0.6.2
einops==0.8.0
encodec==0.1.1
executing==2.1.0
fastjsonschema==2.21.1
filelock==3.16.1
Flask==3.1.0
fonttools==4.55.3
fqdn==1.5.1
frozenlist==1.5.0
fsspec==2024.12.0
fugashi==1.4.0
g2pkk==0.1.2
grpcio==1.68.1
gruut==2.2.3
gruut-ipa==0.13.0
gruut-lang-de==2.0.1
gruut-lang-en==2.0.1
gruut-lang-es==2.0.1
gruut-lang-fr==2.0.2
h11==0.14.0
hangul-romanize==0.1.0
httpcore==1.0.7
httpx==0.28.1
huggingface-hub==0.27.0
idna==3.10
inflect==7.4.0
ipykernel==6.29.5
ipython==8.31.0
isoduration==20.11.0
isort==5.13.2
itsdangerous==2.2.0
jaconv==0.4.0
jamo==0.4.1
jedi==0.19.2
jieba==0.42.1
Jinja2==3.1.4
joblib==1.4.2
json5==0.10.0
jsonlines==1.2.0
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
kiwisolver==1.4.7
langcodes==3.5.0
language_data==1.3.0
lazy-object-proxy==1.10.0
lazy_loader==0.4
librosa==0.10.2.post1
llvmlite==0.43.0
marisa-trie==1.2.1
Markdown==3.7
markdown-it-py==3.0.0
MarkupSafe==3.0.2
matplotlib==3.10.0
matplotlib-inline==0.1.7
mccabe==0.6.1
mdurl==0.1.2
mecab-python3==1.0.6
mistune==3.0.2
mojimoji==0.0.13
more-itertools==10.5.0
mpmath==1.3.0
msgpack==1.1.0
multidict==6.1.0
murmurhash==1.0.11
mutagen==1.47.0
mypy-extensions==1.0.0
nbclient==0.10.2
nbconvert==7.16.4
nbformat==5.10.4
nest-asyncio==1.6.0
networkx==2.8.8
nltk==3.9.1
nose2==0.15.1
notebook==7.3.2
notebook_shim==0.2.4
num2words==0.5.14
numba==0.60.0
numpy==1.26.4
nvidia-cublas-cu12==12.4.5.8
nvidia-cuda-cupti-cu12==12.4.127
nvidia-cuda-nvrtc-cu12==12.4.127
nvidia-cuda-runtime-cu12==12.4.127
nvidia-cudnn-cu12==9.1.0.70
nvidia-cufft-cu12==11.2.1.3
nvidia-curand-cu12==10.3.5.147
nvidia-cusolver-cu12==11.6.1.9
nvidia-cusparse-cu12==12.3.1.170
nvidia-nccl-cu12==2.21.5
nvidia-nvjitlink-cu12==12.4.127
nvidia-nvtx-cu12==12.4.127
overrides==7.7.0
packaging==24.2
pandas==1.5.3
pandocfilters==1.5.1
parso==0.8.4
pathspec==0.12.1
pexpect==4.9.0
pillow==11.0.0
platformdirs==4.3.6
pooch==1.8.2
preshed==3.0.9
prometheus_client==0.21.1
prompt_toolkit==3.0.48
propcache==0.2.1
protobuf==5.29.2
psutil==6.1.1
ptyprocess==0.7.0
pure_eval==0.2.3
pycparser==2.22
pydantic==2.10.4
pydantic_core==2.27.2
Pygments==2.18.0
pylint==2.10.2
pynndescent==0.5.13
pyparsing==3.2.0
pypinyin==0.53.0
pysbd==0.3.4
python-crfsuite==0.9.11
python-dateutil==2.9.0.post0
python-json-logger==3.2.1
pytz==2024.2
PyYAML==6.0.2
pyzmq==26.2.0
referencing==0.35.1
regex==2024.11.6
requests==2.32.3
rfc3339-validator==0.1.4
rfc3986-validator==0.1.1
rich==13.9.4
rpds-py==0.22.3
safetensors==0.4.5
scikit-learn==1.6.0
scipy==1.14.1
Send2Trash==1.8.3
shellingham==1.5.4
six==1.17.0
smart-open==7.1.0
sniffio==1.3.1
soundfile==0.12.1
soupsieve==2.6
soxr==0.5.0.post1
spacy==3.8.3
spacy-legacy==3.0.12
spacy-loggers==1.0.5
srsly==2.5.0
stack-data==0.6.3
SudachiDict-core==20241021
SudachiPy==0.6.9
sympy==1.13.1
tensorboard==2.18.0
tensorboard-data-server==0.7.2
terminado==0.18.1
thinc==8.3.3
threadpoolctl==3.5.0
tinycss2==1.4.0
tokenizers==0.21.0
toml==0.10.2
torch==2.5.1
torchaudio==2.5.1
tornado==6.4.2
tqdm==4.67.1
trainer==0.0.36
traitlets==5.14.3
transformers==4.47.1
triton==3.1.0
typeguard==4.4.1
typer==0.15.1
types-python-dateutil==2.9.0.20241206
typing_extensions==4.12.2
tzlocal==5.2
umap-learn==0.5.7
Unidecode==1.3.8
unidic-lite==1.0.8
uri-template==1.3.0
urllib3==2.2.3
wasabi==1.1.3
wcwidth==0.2.13
weasel==0.4.1
webcolors==24.11.1
webencodings==0.5.1
websocket-client==1.8.0
Werkzeug==3.1.3
wrapt==1.12.1
yarl==1.18.3
'''