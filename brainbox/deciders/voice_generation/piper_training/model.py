from typing import *
from dataclasses import dataclass
from pathlib import Path
from ....framework import DownloadableModel, IController
from ...common import download_file


@dataclass
class PiperTrainingModel(DownloadableModel):
    name: str
    url: str

    def get_local_location(self, controller: IController) -> Path:
        return controller.resource_folder('base_models')/self.name

    @classmethod
    def download(cls, models: list['DownloadableModel'], controller: IController):
        for model in models:
            model = cast(PiperTrainingModel, model)
            download_file(model.url, controller.resource_folder('base_models')/model.name)
