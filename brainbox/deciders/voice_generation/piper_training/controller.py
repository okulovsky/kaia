import json
import os
from unittest import TestCase
from brainbox.framework import Loc, RunConfiguration
from foundation_kaia.brainbox_utils import Installer
from foundation_kaia.marshalling_2 import TypeTools
from .app.interface import CkptData
from .settings import PiperTrainingSettings
from ...common import VOICEOVER_TEXT
from brainbox.framework.controllers.self_test.self_test_case import check_if_its_sound
from pprint import pprint

from ....framework import (
    SmallImageBuilder, IImageBuilder,
    BrainBoxApi, BrainBoxTask, File,
    DockerMarshallingController, BrainboxImageBuilder
)
from pathlib import Path
import zipfile
from .app.installer import PiperTrainingInstaller


class PiperTrainingController(DockerMarshallingController[PiperTrainingSettings]):
    def get_installer(self) -> Installer|None:
        return PiperTrainingInstaller(self.resource_folder())

    def get_image_builder(self) -> IImageBuilder|None:
        return BrainboxImageBuilder(
            Path(__file__).parent,
            '3.10.18',
            repository=BrainboxImageBuilder.Repository(
                'https://github.com/rhasspy/piper',
                pip_install_options='--no-deps -e',
                commit='73c04d81d5590ecc46e522de3601ce7fb29fc2be',
                path_to_package='src/python',
                remove_files=(
                    'src/python/requirements.txt',
                ),
                post_install_commands=(
                    'cd /home/app/repo/src/python && python3 piper_train/vits/monotonic_align/setup.py build_ext --inplace',
                )
            ),
            dependencies=(
                BrainboxImageBuilder.PytorchDependencies('2.7.1', 'cu128', True),
                BrainboxImageBuilder.RequirementsLockTxt(True),
                BrainboxImageBuilder.KaiaFoundationDependencies()
            ),
            keep_dockerfile=True
        )

    def get_service_run_configuration(self, parameter: str|None) -> RunConfiguration:
        return RunConfiguration(
            publish_ports={self.connection_settings.port:8080},
        )


    def create_api(self):
        from .api import PiperTrainingApi
        return PiperTrainingApi()

    def custom_self_test(self, api: BrainBoxApi, tc: TestCase):
        from .api import PiperTraining
        from ..piper import Piper

        NAME = 'piper_voice_training_dataset'

        #preparing zip-file in a dataset format
        src_folder = Path(__file__).parent/'files'
        dataset = Loc.test_folder/(NAME+'.zip')
        with zipfile.ZipFile(dataset, 'w') as zip:
            for file in os.listdir(src_folder):
                for instance in range(100):
                    zip.write(src_folder/file, f'voice/{instance}-'+file)

        task = PiperTraining.new_task().train(
            NAME,
            PiperTraining.Models.lessac,
            PiperTraining.TrainingParameters(),
            dataset
        )

        id = None
        try:
            id = api.add(task)
            log_file = api.join(id)
        except Exception:
            if id is not None:
                pprint(api.tasks.get_log(id))
            raise

        lines = api.cache.read_file(log_file).string_content.split('\n')
        ckpt = None
        for line in lines:
            if len(line.strip()) > 0:
                js = json.loads(line)
                if js['result'] is not None:
                    print(js)
                    ckpt = TypeTools.deserialize(js['result'], list[CkptData])[0]

        onnx = api.execute(PiperTraining.new_task().export(ckpt))

        api.execute(Piper.new_task().upload_tar_voice(onnx, NAME))
        voice_result = api.execute(Piper.new_task().voiceover(VOICEOVER_TEXT, NAME))
        check_if_its_sound(api.cache.read_file(voice_result).content, tc)

        api.execute(Piper.new_task().delete_voice(NAME))



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

"""

#This recepy worked https://github.com/rhasspy/piper/issues/295 (up to lightning update)