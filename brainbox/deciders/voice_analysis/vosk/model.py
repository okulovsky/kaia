import os
import shutil
from typing import cast
from pathlib import Path
import zipfile

from ....framework import DownloadableModel, IController
from ...common import download_file
from dataclasses import dataclass

@dataclass
class VoskModel(DownloadableModel):
    name: str
    url: str

    def get_local_location(self, controller: IController) -> Path:
        return controller.resource_folder('models')/self.name

    @classmethod
    def download(cls, models: list['DownloadableModel'], controller: IController):
        for model in models:
            model = cast(VoskModel, model)
            zip_file_path = controller.resource_folder('models')/(model.name+'.zip')
            download_file(
                model.url,
                zip_file_path
            )
            model_path = controller.resource_folder('models')/model.name
            shutil.rmtree(model_path, ignore_errors=True)
            os.makedirs(model_path)
            with zipfile.ZipFile(zip_file_path, 'r') as zip_file:
                zip_file.extractall(model_path)
            inner_folder = os.listdir(model_path)
            if len(inner_folder) != 1:
                raise ValueError(f"after unzipping, only one folder was expected, but was {inner_folder}")
            for item in (model_path/inner_folder[0]).iterdir():
                shutil.move(str(item), str(model_path))
            os.unlink(zip_file_path)


