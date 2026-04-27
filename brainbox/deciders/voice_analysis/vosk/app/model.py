import os
import shutil
import zipfile
from dataclasses import dataclass
from pathlib import Path

from foundation_kaia.brainbox_utils import Installer, download_file


@dataclass
class VoskModelSpec:
    url: str


class VoskInstaller(Installer[VoskModelSpec]):
    def _execute_installation(self):
        pass

    def _execute_model_downloading(self, model: str, model_spec: VoskModelSpec):
        models_dir = self.resources_folder / 'models'
        models_dir.mkdir(parents=True, exist_ok=True)
        zip_file_path = models_dir / (model + '.zip')
        download_file(model_spec.url, zip_file_path)
        model_path = models_dir / model
        shutil.rmtree(model_path, ignore_errors=True)
        os.makedirs(model_path)
        with zipfile.ZipFile(zip_file_path, 'r') as zip_file:
            zip_file.extractall(model_path)
        inner_folder = os.listdir(model_path)
        if len(inner_folder) != 1:
            raise ValueError(f"after unzipping, only one folder was expected, but was {inner_folder}")
        for item in (model_path / inner_folder[0]).iterdir():
            shutil.move(str(item), str(model_path))
        shutil.rmtree(model_path / inner_folder[0], ignore_errors=True)
        os.unlink(zip_file_path)

    def _execute_model_loading(self, model: str, model_spec: VoskModelSpec):
        from vosk import Model, SetLogLevel
        SetLogLevel(-1)
        return Model(str(self.resources_folder / 'models' / model))
