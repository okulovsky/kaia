from typing import *
from pathlib import Path
from .settings import RhasspyKaldiSettings
from ..arch import LocalImageInstaller, DockerService, BrainBoxServiceRunner
from .api import RhasspyKaldi
from unittest import TestCase
import requests
import json
from .tests import english, german, english_custom

class RhasspyKaldiInstaller(LocalImageInstaller):
    def __init__(self, settings: RhasspyKaldiSettings):
        self.settings = settings


        service = DockerService(
            self, self.settings.port, self.settings.startup_timeout_in_seconds,
            BrainBoxServiceRunner(
                mount_resource_folders={'profiles': '/profiles', 'models': '/models'},
                publish_ports={self.settings.port: 8084}
            )
        )

        super().__init__(
            'rhasspy_kaldi',
            Path(__file__).parent / 'container',
            DOCKERFILE,
            None,
            service)

        self.notebook_service = service.as_notebook_service()
        self.notebook_service._container_runner.run_as_root = True

    def _create_installation_service(self, language):
        service = DockerService(
            self, self.settings.port, self.settings.startup_timeout_in_seconds,
            BrainBoxServiceRunner(
                mount_resource_folders={'profiles': '/profiles', 'models': '/models'},
                publish_ports={self.settings.port: 12101},
                custom_flags=['-v', '/etc/localtime:/etc/localtime:ro'],
                command_line_arguments=['--rhasspy','--language',language],
            )
        )
        return service

    def post_install(self):
        for language in self.settings.languages:
            profile_folder = self.resource_folder('profiles')
            folder = profile_folder/language
            if folder.is_dir():
                continue
            print(f'LANGUAGE {language}')
            self.executor.upload_file(
                Path(__file__).parent / 'files/default_profile.json',
                str(self.resource_folder('profiles', language) / 'profile.json')
            )
            service = self._create_installation_service(language)
            service.run()
            service.wait_for_running()
            requests.post(f'http://{self.ip_address}:{self.settings.port}/api/download-profile')
            service.kill()


    def create_api(self):
        return RhasspyKaldi(f'{self.ip_address}:{self.settings.port}')

    def warmup(self, parameters: str):
        self.run_if_not_running_and_wait()

    def _brainbox_self_test_internal(self, api, tc: TestCase) -> Iterable:
        self.run_if_not_running_and_wait()
        yield from english(api, tc)
        yield from german(api, tc)
        yield from english_custom(api, tc)



    def create_brainbox_decider_api(self, parameters: str):
        return RhasspyKaldi(f'{self.ip_address}:{self.settings.port}', parameters)


DOCKERFILE = f'''
FROM rhasspy/rhasspy

RUN /usr/lib/rhasspy/.venv/bin/pip install notebook flask

COPY . /home/app

ENTRYPOINT ["/usr/lib/rhasspy/.venv/bin/python", "/home/app/main.py"] 
'''
