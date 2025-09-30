from typing import Iterable
from unittest import TestCase
from ....framework import (
    RunConfiguration, TestReport, SmallImageBuilder, IImageBuilder,
    BrainBoxApi, BrainBoxTask, File,
    OnDemandDockerController
)
from .settings import BoilerplateOnDemandSettings
from pathlib import Path



class BoilerplateOnDemandController(OnDemandDockerController[BoilerplateOnDemandSettings]):
    def get_image_builder(self) -> IImageBuilder|None:
        return SmallImageBuilder(
            Path(__file__).parent/'container',
            DOCKERFILE,
            DEPENDENCIES.split('\n'),
        )

    def get_default_settings(self):
        return BoilerplateOnDemandSettings()

    def create_api(self):
        from .api import BoilerplateOnDemand
        return BoilerplateOnDemand()

    def _self_test_internal(self, api: BrainBoxApi, tc: TestCase) -> Iterable:
        from .api import BoilerplateOnDemand

        result = api.execute(BrainBoxTask.call(BoilerplateOnDemand).execute('test input'))
        tc.assertEqual('output test input', result)
        yield TestReport.last_call(api).href('run')


DOCKERFILE = f"""
FROM python:3.11.11

{{{SmallImageBuilder.ADD_USER_PLACEHOLDER}}}

WORKDIR /home/app

{{{SmallImageBuilder.PIP_INSTALL_PLACEHOLDER}}}

COPY . /home/app

ENTRYPOINT ["python3", "/home/app/main.py"]
"""

DEPENDENCIES = """
python-dotenv==1.0.1
"""