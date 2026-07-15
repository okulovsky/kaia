import time
from typing import Iterable
from unittest import TestCase
import json

from foundation_kaia.brainbox_utils import Installer
from ....framework import (
    RunConfiguration, TestReport, BrainboxImageBuilder, IImageBuilder, DockerMarshallingController,
    BrainBoxApi, BrainBoxTask, SelfTestCase, logger
)
from .settings import HelloBrainBoxSettings
from pathlib import Path
from .app.model import HelloBrainBoxInstaller


class HelloBrainBoxController(DockerMarshallingController[HelloBrainBoxSettings]):
    def get_image_builder(self) -> IImageBuilder|None:
        return BrainboxImageBuilder(
            Path(__file__).parent,
            '3.11.11',
            dependencies=(
                BrainboxImageBuilder.RequirementsLockTxt(),
            )
        )

    def get_service_run_configuration(self, port: int, parameter: str | None) -> RunConfiguration:
        return RunConfiguration(
            parameter,
            publish_ports={port:8080},
            command_line_arguments=[parameter] if parameter is not None else [],
        )

    def get_installer(self) -> Installer|None:
        return HelloBrainBoxInstaller(self.resource_folder())

    def get_default_settings(self):
        return HelloBrainBoxSettings()

    def get_loading_time_in_seconds(self) -> int:
        return 5

    def create_api(self, base_url: str):
        from .api import HelloBrainBoxApi
        return HelloBrainBoxApi(base_url)

    def self_test_cases(self) -> Iterable[SelfTestCase]:
        from .api import HelloBrainBox
        yield SelfTestCase(
            HelloBrainBox.new_task().sum(2, 4),
            SelfTestCase.assertEqual(6.0)
        )
        yield SelfTestCase(
            HelloBrainBox.new_task().voiceover('test', 'google'),
            SelfTestCase.assertFileJsonEqual({"text": "test", "model": "[LOADED] /resources/models/google"})
        )
        yield SelfTestCase(
            HelloBrainBox.new_task().voice_embedding(b'12121'),
            SelfTestCase.assertEqual([0,3,2,0,0,0,0,0,0,0])
        )
        yield SelfTestCase(
            HelloBrainBox.new_task().stream_voiceover([dict(text='a'), dict(text='b')]),
            SelfTestCase.assertFileContentEqual(b'{"token": "a"}{"token": "b"}')
        )

    def custom_self_test(self, api, tc: TestCase):
        from .api import HelloBrainBox

        training_id = api.add(HelloBrainBox.new_task().training(b'abcd'))
        while True:
            status = api.jobs.get_job_summary(training_id)
            if status.progress is not None and status.progress > 0:
                break
            time.sleep(0.1)
        log = api.jobs.get_job(training_id).log
        tc.assertIsNotNone(log)
        tc.assertGreater(len(log), 0)
        result_file = api.join(training_id)
        lines = api.cache.read_file(result_file).string_content.split('\n')

        print(lines)
        final_result = None
        for line in lines:
            if line.strip():
                js = json.loads(line)
                print(js)
                if js.get('result') is not None:
                    final_result = js['result']
        tc.assertEqual('RESULT', final_result)
        logger.last_call(api)

        failing_id = api.add(HelloBrainBox.new_task().training(b'abcd', raise_exception=True))
        while True:
            status = api.jobs.get_job_summary(failing_id)
            if status.finished_timestamp is not None:
                break
            time.sleep(0.1)
        tc.assertFalse(status.success)
        tc.assertIsNotNone(api.jobs.get_job(failing_id).error)
        logger.last_call(api)










