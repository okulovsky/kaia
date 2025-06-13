from typing import Iterable
from unittest import TestCase

from ....framework import (
    TestReport, SmallImageBuilder, IImageBuilder,
    BrainBoxApi, BrainBoxTask,
    OnDemandDockerController
)
from .settings import WhisperXSettings
from pathlib import Path



class WhisperXController(OnDemandDockerController[WhisperXSettings]):
    def get_image_builder(self) -> IImageBuilder|None:
        return SmallImageBuilder(
            Path(__file__).parent/'container',
            DOCKERFILE,
            DEPENDENCIES.split('\n'),
        )

    def get_default_settings(self):
        return WhisperXSettings()

    def create_api(self):
        from .api import WhisperX
        return WhisperX()

    def _self_test_internal(self, api: BrainBoxApi, tc: TestCase) -> Iterable:
        from .api import WhisperX

        filename = 'dubai.mp4'
        api.execute(BrainBoxTask.call(WhisperX).execute(filename))
        yield TestReport.last_call(api).href('run')




DOCKERFILE = f"""
FROM python:3.11

{SmallImageBuilder.APT_INSTALL('ffmpeg')}

{{{SmallImageBuilder.ADD_USER_PLACEHOLDER}}}

WORKDIR /home/app

{{{SmallImageBuilder.PIP_INSTALL_PLACEHOLDER}}}

COPY . .

ENTRYPOINT ["python3", "/home/app/main.py"]
"""

DEPENDENCIES = """
whisperx==3.3.4
lightning_fabric==2.0.4
hf_xet==1.1.2
"""