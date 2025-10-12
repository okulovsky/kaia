from typing import Iterable
from unittest import TestCase
from ....framework import (
    RunConfiguration, TestReport, BrainboxImageBuilder, IImageBuilder,
    BrainBoxApi, BrainBoxTask, File,
    OnDemandDockerController
)
from .settings import BoilerplateOnDemandSettings
from pathlib import Path



class BoilerplateOnDemandController(OnDemandDockerController[BoilerplateOnDemandSettings]):
    def get_image_builder(self) -> IImageBuilder|None:
        return BrainboxImageBuilder(
            Path(__file__).parent,
            '3.11.11',
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

