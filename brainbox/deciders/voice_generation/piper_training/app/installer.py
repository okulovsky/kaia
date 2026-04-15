from foundation_kaia.brainbox_utils import Installer, download_file
from dataclasses import dataclass
from pathlib import Path

@dataclass
class PiperTrainingModel:
    url: str
    epoch: int
    language: str

class PiperTrainingInstaller(Installer[PiperTrainingModel]):
    def __init__(self, resource_folder: Path):
        super().__init__(resource_folder)
    
    @property
    def base_models_folder(self):
        return self.resources_folder/'base_models'

    def _execute_model_downloading(self, model: str, model_spec: PiperTrainingModel):
        download_file(model_spec.url, self.base_models_folder/model)

