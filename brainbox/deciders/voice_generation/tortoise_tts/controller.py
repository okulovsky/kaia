from typing import Iterable
from unittest import TestCase
from ....framework import (
    RunConfiguration, TestReport, SmallImageBuilder, IImageBuilder, DockerWebServiceController,
    BrainBoxApi, BrainBoxTask, File, INotebookableController
)
from ...common import VOICEOVER_TEXT, check_if_its_sound
from .settings import TortoiseTTSSettings
from pathlib import Path


class TortoiseTTSController(DockerWebServiceController[TortoiseTTSSettings], INotebookableController):
    def get_image_builder(self) -> IImageBuilder|None:
        return SmallImageBuilder(
            Path(__file__).parent/'container',
            DOCKERFILE,
            DEPENDENCIES.split("\n")
        )

    def get_service_run_configuration(self, parameter: str|None) -> RunConfiguration:
        if parameter is not None:
            raise ValueError(f"`parameter` must be None for {self.get_name()}")
        return RunConfiguration(
            parameter,
            publish_ports={self.connection_settings.port: 8084},
            mount_resource_folders=dict(
                voices='/home/app/tortoise-tts/tortoise/voices',
                hf_models='/home/app/.cache/huggingface/hub/',
                tortoise_models='/home/app/.cache/tortoise/models',
                stash='/stash',
            ),
        )

    def get_notebook_configuration(self) -> RunConfiguration|None:
        return self.get_service_run_configuration(None).as_notebook_service()

    def get_default_settings(self):
        return TortoiseTTSSettings()

    def create_api(self):
        from .api import TortoiseTTS
        return TortoiseTTS()

    def post_install(self):
        should_install = False
        for model in [
            self.resource_folder('hf_models')/'models--facebook--wav2vec2-large-960h',
            self.resource_folder('hf_models')/'models--jbetker--tacotron-symbols',
            self.resource_folder('hf_models')/'models--jbetker--wav2vec2-large-robust-ft-libritts-voxpopuli',
            self.resource_folder('tortoise_models') /'models--Manmay--tortoise-tts'
        ]:
            if not model.is_dir():
                should_install = True
                break
        if should_install:
            self.run_auxiliary_configuration(self.get_service_run_configuration(None).as_service_worker('--install'))


    def _self_test_internal(self, api: BrainBoxApi, tc: TestCase) -> Iterable:
        from .api import TortoiseTTS

        TortoiseTTS.export_voice('test_voice', [Path(__file__).parent/'test_voice.wav']).execute(api)
        text = VOICEOVER_TEXT
        files = api.execute(BrainBoxTask.call(TortoiseTTS).dub(text=text, voice='test_voice'))
        yield TestReport.last_call(api).href('voiceover').result_is_array_of_files(File.Kind.Audio).with_comment("Voiceover")
        for i, fname in enumerate(files):
            file = api.open_file(fname)
            check_if_its_sound(file.content, tc)



DOCKERFILE = f'''
FROM python:3.9.21

{{{SmallImageBuilder.ADD_USER_PLACEHOLDER}}}

{{{SmallImageBuilder.PIP_INSTALL_PLACEHOLDER}}}

WORKDIR /home/app

{SmallImageBuilder.GIT_CLONE_AND_RESET(
    'https://github.com/neonbjb/tortoise-tts.git',
    'tortoise-tts',
    '8a2563ecabe93c4fb626f876dd0c52c966edef2f',
    install=False
)}

COPY . /home/app/tortoise-tts/

WORKDIR /home/app/tortoise-tts

RUN rm setup.py & pip install --user -e .

ENTRYPOINT ["python", "/home/app/tortoise-tts/main.py"]

'''


DEPENDENCIES = '''
--extra-index-url https://download.pytorch.org/whl/cu121
appdirs==1.4.4
asttokens==3.0.0
attrs==24.3.0
audioread==3.0.1
bleach==6.2.0
blinker==1.9.0
blis==0.7.11
catalogue==2.0.10
certifi==2024.12.14
cffi==1.17.1
charset-normalizer==3.4.0
click==8.1.8
cloudpathlib==0.20.0
confection==0.1.5
cymem==2.0.10
debugpy==1.8.11
decorator==5.1.1
deepspeed==0.8.3
einops==0.4.1
entrypoints==0.4
exceptiongroup==1.2.2
executing==2.1.0
fastjsonschema==2.21.1
ffmpeg==1.4
filelock==3.16.1
Flask==3.1.0
fsspec==2024.12.0
hjson==3.1.0
huggingface-hub==0.27.0
idna==3.10
importlib_metadata==8.5.0
inflect==7.4.0
ipykernel==6.9.2
ipython==8.18.1
ipython-genutils==0.2.0
itsdangerous==2.2.0
jedi==0.19.2
Jinja2==3.1.5
joblib==1.4.2
jsonschema==4.23.0
jsonschema-specifications==2024.10.1
jupyter-client==7.1.2
jupyter_core==5.7.2
langcodes==3.5.0
language_data==1.3.0
librosa==0.9.1
llvmlite==0.43.0
marisa-trie==1.2.1
markdown-it-py==3.0.0
MarkupSafe==3.0.2
matplotlib-inline==0.1.7
mdurl==0.1.2
mistune==3.0.2
more-itertools==10.5.0
mpmath==1.3.0
murmurhash==1.0.11
nbconvert==5.3.1
nbformat==5.10.4
nest-asyncio==1.6.0
networkx==3.2.1
ninja==1.11.1.3
notebook==5.7.13
numba==0.60.0
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
nvidia-nvjitlink-cu12==12.6.85
nvidia-nvtx-cu12==12.1.105
packaging==24.2
pandocfilters==1.5.1
parso==0.8.4
pexpect==4.9.0
pillow==11.0.0
platformdirs==4.3.6
pooch==1.8.2
preshed==3.0.9
progressbar==2.5
prometheus_client==0.21.1
prompt_toolkit==3.0.48
psutil==6.1.1
ptyprocess==0.7.0
pure_eval==0.2.3
py-cpuinfo==9.0.0
pycparser==2.22
pydantic==1.9.1
Pygments==2.18.0
python-dateutil==2.9.0.post0
PyYAML==6.0.2
pyzmq==26.2.0
referencing==0.35.1
regex==2024.11.6
requests==2.32.3
resampy==0.4.3
rich==13.9.4
rotary-embedding-torch==0.3.6
rpds-py==0.22.3
safetensors==0.4.5
scikit-learn==1.6.0
scipy==1.13.1
Send2Trash==1.8.3
shellingham==1.5.4
six==1.17.0
smart-open==7.1.0
sounddevice==0.5.1
soundfile==0.12.1
spacy==3.7.5
spacy-legacy==3.0.12
spacy-loggers==1.0.5
srsly==2.5.0
stack-data==0.6.3
sympy==1.13.3
terminado==0.13.3
testpath==0.6.0
thinc==8.2.5
threadpoolctl==3.5.0
tokenizers==0.13.3
torch==2.2.2+cu121
torchaudio==2.2.2+cu121
torchvision==0.17.2+cu121
tornado==4.2
tqdm==4.67.1
traitlets==5.14.3
transformers==4.31.0
triton==2.2.0
typeguard==4.4.1
typer==0.15.1
typing_extensions==4.12.2
Unidecode==1.3.8
urllib3==2.3.0
wasabi==1.1.3
wcwidth==0.2.13
weasel==0.4.1
webencodings==0.5.1
Werkzeug==3.1.3
wrapt==1.17.0
zipp==3.21.0
'''