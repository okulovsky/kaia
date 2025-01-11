from pathlib import Path

from ....framework import DownloadableModel, IController
from dataclasses import dataclass
from typing import cast

@dataclass
class YoloModel(DownloadableModel):
    repo_id: str
    file_name: str

    @property
    def model_id(self):
        return f'{self.repo_id}:{self.file_name}'

    def get_local_location(self, controller: IController) -> Path:
        return controller.resource_folder('models')/self.repo_id/self.file_name

    @classmethod
    def download(cls, models: list['DownloadableModel'], controller: IController):
        from .controller import YoloController
        from .api import Yolo
        controller = cast(YoloController, controller)
        instance_id = controller.run(None)
        api: Yolo = controller.find_api(instance_id)
        for model in models:
            model = cast(YoloModel, model)
            api.load_model(model.model_id)
        controller.stop(instance_id)
