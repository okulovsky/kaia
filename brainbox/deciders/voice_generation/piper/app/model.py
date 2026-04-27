from dataclasses import dataclass

from foundation_kaia.brainbox_utils import Installer, TModelSpec, download_file


@dataclass
class PiperModelSpec:
    config_url: str
    url: str


class PiperInstaller(Installer[PiperModelSpec]):
    def _execute_installation(self):
        pass

    def _execute_model_downloading(self, model: str, model_spec: PiperModelSpec):
        download_file(model_spec.config_url, self.resources_folder / 'models' / (model + '.onnx.json'))
        download_file(model_spec.url, self.resources_folder / 'models' / (model + '.onnx'))
