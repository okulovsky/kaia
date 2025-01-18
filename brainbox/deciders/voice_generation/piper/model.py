from typing import cast
from dataclasses import dataclass
from pathlib import Path

from ....framework import DownloadableModel, IController
from ...common import download_file


@dataclass
class PiperModel(DownloadableModel):
    name: str
    config_url: str
    url: str

    def get_local_location(self, controller: IController) -> Path:
        return controller.resource_folder()/'models'/(self.name+'.onnx')

    @classmethod
    def download(cls, models: list['DownloadableModel'], controller: IController):
        from .controller import PiperController
        controller = cast(PiperController, controller)
        path = controller.resource_folder('models')
        for model in models:
            model = cast(PiperModel, model)
            download_file(model.config_url, path/(model.name+'.onnx.json'))
            download_file(model.url, path/(model.name+'.onnx'))