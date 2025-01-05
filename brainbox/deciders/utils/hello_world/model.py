from pathlib import Path
from typing import cast
from ....framework import DownloadableModel, IController, FileIO
from dataclasses import dataclass
import requests

@dataclass
class HelloBrainBoxModel(DownloadableModel):
    name: str
    url: str

    def get_local_location(self, controller: IController) -> Path:
        return controller.resource_folder('models')/self.name

    @classmethod
    def download(cls, models: list['DownloadableModel'], controller: IController):
        for model in models:
            model = cast(HelloBrainBoxModel, model)
            reply = requests.get(model.url)
            FileIO.write_bytes(reply.content, model.get_local_location(controller))
