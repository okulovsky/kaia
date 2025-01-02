from pathlib import Path
from typing import cast
from ....framework import DownloadableModel, IController, RunConfiguration
from dataclasses import dataclass
import shutil
import requests

@dataclass
class RhasspyKaldiModel(DownloadableModel):
    language: str

    def get_local_location(self, controller: IController) -> Path:
        profile_folder = controller.resource_folder('profiles')
        folder = profile_folder / self.language
        return folder

    def download(cls, models: list['DownloadableModel'], controller: IController):
        from .controller import RhasspyKaldiController
        controller = cast(RhasspyKaldiController, controller)
        for model in models:
            model = cast(RhasspyKaldiModel, model)
            shutil.copy(
                Path(__file__).parent / 'files/default_profile.json',
                controller.resource_folder('profiles', model.language) / 'profile.json'
            )
            cfg = RunConfiguration(
                None,
                mount_resource_folders={'profiles': '/profiles', 'models': '/models'},
                publish_ports={controller.settings.connection.port: 12101},
                custom_flags=['-v', '/etc/localtime:/etc/localtime:ro'],
                command_line_arguments=['--rhasspy', '--language', model.language],
            )
            instance_id = controller.run_with_configuration(cfg)
            controller.wait_for_boot()
            requests.post(f'http://127.0.0.1:{controller.settings.connection.port}/api/download-profile')
            controller.stop(instance_id)


