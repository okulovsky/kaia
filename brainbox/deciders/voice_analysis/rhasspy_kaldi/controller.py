import shutil
from typing import Iterable
from unittest import TestCase
from ....framework import (
    RunConfiguration, TestReport, SmallImageBuilder,
    IImageBuilder, DockerWebServiceController, BrainBoxApi
)
from .settings import RhasspyKaldiSettings
from pathlib import Path
import requests


class RhasspyKaldiController(DockerWebServiceController[RhasspyKaldiSettings]):
    def get_image_builder(self) -> IImageBuilder|None:
        return SmallImageBuilder(
            Path(__file__).parent/'container',
            DOCKERFILE,
            None
        )

    def get_service_run_configuration(self, parameter: str|None) -> RunConfiguration:
        if parameter is not None:
            raise ValueError(f"`parameter` must be None for {self.get_name()}")
        return RunConfiguration(
            None,
            mount_resource_folders={'profiles': '/profiles', 'models': '/models'},
            publish_ports={self.settings.connection.port: 8084}
        )

    def get_notebook_configuration(self) -> RunConfiguration|None:
        return self.get_service_run_configuration(None).as_notebook_service()

    def get_default_settings(self):
        return RhasspyKaldiSettings()

    def create_api(self):
        from .api import RhasspyKaldi
        return RhasspyKaldi()

    def run_notebook(self):
        self.run_with_configuration(self.get_service_run_configuration(None).as_notebook_service())

    def post_install(self):
        for language in self.settings.languages:
            self.context.logger.log(f"Installing the base model for the language {language}")
            profile_folder = self.resource_folder('profiles')
            folder = profile_folder/language
            if folder.is_dir():
                continue
            print(f'LANGUAGE {language}')
            shutil.copy(
                Path(__file__).parent / 'files/default_profile.json',
                self.resource_folder('profiles', language) / 'profile.json'
            )
            cfg = RunConfiguration(
                None,
                mount_resource_folders={'profiles': '/profiles', 'models': '/models'},
                publish_ports={self.settings.connection.port: 12101},
                custom_flags=['-v', '/etc/localtime:/etc/localtime:ro'],
                command_line_arguments=['--rhasspy', '--language', language],
            )
            instance_id = self.run_with_configuration(cfg)
            self.wait_for_boot()
            requests.post(f'http://127.0.0.1:{self.settings.connection.port}/api/download-profile')
            self.stop(instance_id)

    def _self_test_internal(self, api: BrainBoxApi, tc: TestCase) -> Iterable[TestReport.Item]:
        from .tests import english, german, english_custom
        yield from english(api, tc)
        yield from german(api, tc)
        yield from english_custom(api, tc)


DOCKERFILE = f'''
FROM rhasspy/rhasspy

RUN /usr/lib/rhasspy/.venv/bin/pip install notebook flask

COPY . /home/app

ENTRYPOINT ["/usr/lib/rhasspy/.venv/bin/python", "/home/app/main.py"] 
'''


