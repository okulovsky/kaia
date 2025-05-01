
import os
from typing import Iterable
from unittest import TestCase
from brainbox.framework import Loc, FileIO, DownloadableModel
from .model import PiperTrainingModel
from ...common import VOICEOVER_TEXT, check_if_its_sound

from ....framework import (
    TestReport, SmallImageBuilder, IImageBuilder,
    BrainBoxApi, BrainBoxTask, File,
    OnDemandDockerController, IModelDownloadingController
)
from .settings import PiperTrainingSettings
from pathlib import Path
import zipfile



class PiperTrainingController(OnDemandDockerController[PiperTrainingSettings], IModelDownloadingController):
    def get_image_builder(self) -> IImageBuilder|None:
        return SmallImageBuilder(
            Path(__file__).parent/'container',
            DOCKERFILE,
            DEPENDENCIES.split('\n'),
        )

    def get_default_settings(self):
        return PiperTrainingSettings()

    def get_downloadable_model_type(self) -> type[DownloadableModel]:
        return PiperTrainingModel

    def create_api(self):
        from .api import PiperTraining
        return PiperTraining()

    def post_install(self):
        self.download_models(self.settings.models_to_download)

    def _self_test_internal(self, api: BrainBoxApi, tc: TestCase) -> Iterable:
        from .api import PiperTraining
        from ..piper import Piper

        NAME  = 'piper_voice_training_dataset'

        #preparing zip-file in a dataset format
        src_folder = Path(__file__).parent/'files'
        dataset = Loc.test_folder/(NAME+'.zip')
        with zipfile.ZipFile(dataset, 'w') as zip:
            for file in os.listdir(src_folder):
                for instance in range(100):
                    zip.write(src_folder/file, f'voice/{instance}-'+file)

        task = PiperTraining.create_training_pack(
            dataset,
            PiperTraining.TrainingSettings(),
            clean_up_afterwards=False,
            reset_if_existing=True
        )
        result = api.execute(task)
        yield TestReport.last_call(api).href('training')

        Piper.UploadVoice(api.cache_folder/result[0]['onnx'], custom_name=NAME).execute(api)
        voice_result = api.execute(BrainBoxTask.call(Piper).voiceover(VOICEOVER_TEXT, NAME))
        check_if_its_sound(api.open_file(voice_result).content, tc)
        yield TestReport.last_call(api).href('inference').result_is_file(File.Kind.Audio)

        Piper.DeleteVoice(NAME).execute(api)



DOCKERFILE = f"""
FROM python:3.9.21

{{{SmallImageBuilder.ADD_USER_PLACEHOLDER}}}

WORKDIR /home/app

{{{SmallImageBuilder.PIP_INSTALL_PLACEHOLDER}}}

{SmallImageBuilder.GIT_CLONE_AND_RESET(
    "https://github.com/rhasspy/piper",
    "piper",
    install=False
)}

RUN rm /home/app/piper/src/python/requirements.txt

RUN sed -i 's/from . import attentions, commons, modules, monotonic_align/from . import attentions, commons, modules\\nimport monotonic_align/' /home/app/piper/src/python/piper_train/vits/models.py

COPY fixes/lightning.py /home/app/piper/src/python/piper_train/vits/lightning.py

COPY fixes/main.py /home/app/piper/src/python/piper_train/__main__.py

WORKDIR /home/app/piper/src/python

RUN pip install --user -e .

COPY . /home/app

ENTRYPOINT ["python3", "/home/app/main.py"]
"""

DEPENDENCIES = """
aiohappyeyeballs==2.4.6
aiohttp==3.11.12
aiosignal==1.3.2
async-timeout==5.0.1
attrs==25.1.0
audioread==3.0.1
certifi==2025.1.31
cffi==1.17.1
charset-normalizer==3.4.1
coloredlogs==15.0.1
Cython==0.29.37
decorator==5.1.1
flatbuffers==25.2.10
frozenlist==1.5.0
fsspec==2025.2.0
humanfriendly==10.0
idna==3.10
joblib==1.4.2
lazy_loader==0.4
librosa==0.10.2.post1
lightning-utilities==0.12.0
llvmlite==0.43.0
monotonic-align==1.0.0
mpmath==1.3.0
msgpack==1.1.0
multidict==6.1.0
numba==0.60.0
numpy==1.26.4
nvidia-cublas-cu11==11.10.3.66
nvidia-cuda-nvrtc-cu11==11.7.99
nvidia-cuda-runtime-cu11==11.7.99
nvidia-cudnn-cu11==8.5.0.96
onnx==1.17.0
onnxruntime==1.19.2
packaging==24.2
piper-phonemize==1.1.0
platformdirs==4.3.6
pooch==1.8.2
propcache==0.2.1
protobuf==5.29.3
pycparser==2.22
pytorch-lightning==1.9.5
PyYAML==6.0.2
requests==2.32.3
scikit-learn==1.6.1
scipy==1.13.1
soundfile==0.13.1
soxr==0.5.0.post1
sympy==1.13.3
threadpoolctl==3.5.0
torch==1.13.1
torchmetrics==1.5.2
tqdm==4.67.1
typing_extensions==4.12.2
urllib3==2.3.0
yarl==1.18.3
"""

#This recepy worked https://github.com/rhasspy/piper/issues/295 (up to lightning update)